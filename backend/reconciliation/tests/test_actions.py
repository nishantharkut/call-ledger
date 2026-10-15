from decimal import Decimal
from io import StringIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from rest_framework.test import APITestCase

from reconciliation.models import BankTransaction, LineItem


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
