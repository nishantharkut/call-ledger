from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from io import StringIO
from threading import Barrier

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import close_old_connections, connection
from django.test import TransactionTestCase, override_settings
from rest_framework.test import APIClient, APITestCase

from reconciliation.models import BankTransaction, LineItem, Match, Organization


class ReconciliationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())

    def upload_payment(self, organization, description, amount, reference):
        content = (
            "date,description,amount,type,reference\n"
            f"2026-04-15,{description},{amount},credit,{reference}\n"
        )
        response = self.client.post(
            "/api/imports/", {"file": SimpleUploadedFile("payment.csv", content.encode())},
            format="multipart", HTTP_X_ORGANIZATION=organization,
        )
        self.assertEqual(response.status_code, 200)
        return BankTransaction.objects.get(
            organization__slug=organization, bank_reference=reference,
        )

    def test_approval_updates_funding_and_cannot_be_repeated(self):
        payment = self.upload_payment("northwind", "Oakridge Holdings", "15000", "OAK-A")
        match = payment.matches.get(line_item__expected_reference="CC-1005")
        url = f"/api/matches/{match.pk}/approve/"
        response = self.client.post(url, HTTP_X_ORGANIZATION="northwind")
        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        match.refresh_from_db()
        item = LineItem.objects.get(pk=match.line_item_id)
        self.assertEqual(item.amount_funded, Decimal("15000.00"))
        self.assertEqual(item.amount_remaining, Decimal("0.00"))
        self.assertEqual(item.status, "funded")
        self.assertEqual(payment.status, "reconciled")
        self.assertEqual(match.status, "approved")
        self.assertEqual(payment.matches.exclude(pk=match.pk).get().status, "rejected")
        response = self.client.post(url, HTTP_X_ORGANIZATION="northwind")
        self.assertEqual(response.status_code, 409)
        item.refresh_from_db()
        self.assertEqual(item.amount_funded, Decimal("15000.00"))

    def test_listings_and_approval_are_isolated_by_organization(self):
        northwind = self.upload_payment("northwind", "CC1001", "1000", "NORTH-A")
        bluebird = self.upload_payment("bluebird", "CC2001", "40000", "BLUE-A")
        for organization, payment, item_count in [
            ("northwind", northwind, 6), ("bluebird", bluebird, 1),
        ]:
            transactions = self.client.get(
                "/api/transactions/", HTTP_X_ORGANIZATION=organization,
            )
            self.assertEqual(transactions.status_code, 200)
            self.assertEqual(transactions.data["count"], 1)
            self.assertEqual(transactions.data["results"][0]["id"], payment.pk)
            self.assertEqual(len(transactions.data["results"][0]["matches"]), 1)
            items = self.client.get("/api/line-items/", HTTP_X_ORGANIZATION=organization)
            self.assertEqual(items.status_code, 200)
            self.assertEqual(len(items.data), item_count)
            self.assertTrue(all(item["organization"] == organization for item in items.data))
        foreign_match = bluebird.matches.get()
        response = self.client.post(
            f"/api/matches/{foreign_match.pk}/approve/", HTTP_X_ORGANIZATION="northwind",
        )
        self.assertEqual(response.status_code, 404)
        foreign_match.line_item.refresh_from_db()
        self.assertEqual(foreign_match.line_item.amount_funded, Decimal("0.00"))

    def test_approval_rechecks_remaining_after_another_payment(self):
        first = self.upload_payment("northwind", "CC1001", "20000", "FIRST")
        second = self.upload_payment("northwind", "CC1001", "20000", "SECOND")
        first_match, second_match = first.matches.get(), second.matches.get()

        approved = self.client.post(
            f"/api/matches/{first_match.pk}/approve/", HTTP_X_ORGANIZATION="northwind",
        )
        stale = self.client.post(
            f"/api/matches/{second_match.pk}/approve/", HTTP_X_ORGANIZATION="northwind",
        )

        self.assertEqual(approved.status_code, 200)
        self.assertEqual(stale.status_code, 409)
        first_match.line_item.refresh_from_db()
        second_match.refresh_from_db()
        self.assertEqual(first_match.line_item.amount_funded, Decimal("20000.00"))
        self.assertEqual(first_match.line_item.status, "partially_funded")
        self.assertEqual(second_match.status, "proposed")

    def test_rejecting_the_last_proposal_requires_review(self):
        payment = self.upload_payment("northwind", "CC1001", "1000", "REJECT")
        match = payment.matches.get()
        response = self.client.post(
            f"/api/matches/{match.pk}/reject/", HTTP_X_ORGANIZATION="northwind",
        )

        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        match.refresh_from_db()
        self.assertEqual(payment.status, "needs_review")
        self.assertTrue(payment.review_reason)
        self.assertEqual(match.status, "rejected")
        self.assertEqual(match.line_item.amount_funded, Decimal("0.00"))

    def test_ignore_rejects_proposals_but_cannot_change_reconciled_payments(self):
        payment = self.upload_payment("northwind", "Oakridge Holdings", "15000", "IGNORE")
        response = self.client.post(
            f"/api/transactions/{payment.pk}/ignore/", HTTP_X_ORGANIZATION="northwind",
        )

        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, "ignored")
        self.assertFalse(payment.matches.exclude(status="rejected").exists())

        reconciled = self.upload_payment("northwind", "CC1001", "1000", "KEEP")
        match = reconciled.matches.get()
        self.assertEqual(self.client.post(
            f"/api/matches/{match.pk}/approve/", HTTP_X_ORGANIZATION="northwind",
        ).status_code, 200)
        refused = self.client.post(
            f"/api/transactions/{reconciled.pk}/ignore/", HTTP_X_ORGANIZATION="northwind",
        )

        self.assertEqual(refused.status_code, 409)
        reconciled.refresh_from_db()
        self.assertEqual(reconciled.status, "reconciled")
        item = LineItem.objects.get(pk=match.line_item_id)
        self.assertEqual(item.amount_funded, Decimal("1000.00"))


@override_settings(AIRTABLE_PAT="", AIRTABLE_BASE_ID="", AIRTABLE_TABLE_NAME="")
class ConcurrentApprovalTests(TransactionTestCase):
    def test_simultaneous_approval_funds_the_line_item_once(self):
        call_command("seed_demo", stdout=StringIO())
        item = LineItem.objects.get(expected_reference="CC-1001")
        payment = BankTransaction.objects.create(
            organization=Organization.objects.get(slug="northwind"),
            date="2026-04-15", description="CC1001", amount=Decimal("1000.00"),
            type="credit", bank_reference="CONCURRENT", status="suggested",
        )
        match = Match.objects.create(
            transaction=payment, line_item=item, reason="Reference CC-1001 found.",
        )
        barrier = Barrier(2)

        def approve():
            # Each request needs its own connection to exercise PostgreSQL row locks.
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return APIClient().post(
                    f"/api/matches/{match.pk}/approve/", HTTP_X_ORGANIZATION="northwind",
                ).status_code
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            requests = [executor.submit(approve) for _ in range(2)]
            statuses = sorted(request.result(timeout=20) for request in requests)

        self.assertEqual(statuses, [200, 409])
        item.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(item.amount_funded, Decimal("1000.00"))
        self.assertEqual(payment.status, "reconciled")
