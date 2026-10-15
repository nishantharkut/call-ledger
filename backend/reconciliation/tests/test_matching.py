import csv
from decimal import Decimal
from io import StringIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from rest_framework.test import APITestCase

from reconciliation.models import BankTransaction, LineItem


class MatchingTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())

    def upload(self, rows):
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["date", "description", "amount", "type", "reference"])
        writer.writerows(rows)
        file = SimpleUploadedFile("payments.csv", output.getvalue().encode("utf-8"))
        response = self.client.post(
            "/api/imports/", {"file": file}, format="multipart",
            HTTP_X_ORGANIZATION="northwind",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["errors"], [])

    def test_reference_matching_accepts_normalized_and_partial_payments(self):
        self.upload([
            ["2026-04-04", "Incoming Haller cc1001", "20000.00", "credit", "HALLER-A"],
            ["2026-04-14", "Incoming wire", "7500.00", "credit", "cc-1001-HALLER-B"],
        ])
        payments = BankTransaction.objects.filter(organization__slug="northwind")
        self.assertEqual(payments.count(), 2)
        for payment in payments:
            self.assertEqual(payment.status, "suggested")
            match = payment.matches.get()
            self.assertEqual(match.line_item.expected_reference, "CC-1001")
            self.assertEqual(match.status, "proposed")
            self.assertIn("Reference CC-1001", match.reason)
            self.assertIn("partial", match.reason.lower())
        self.assertEqual(
            LineItem.objects.get(expected_reference="CC-1001").amount_funded,
            Decimal("0.00"),
        )

    def test_name_and_amount_matching_handles_single_and_multiple_candidates(self):
        self.upload([
            ["2026-04-07", "WIRE / patel family trust", "12500.00", "credit", "PATEL-A"],
            ["2026-04-11", "Wire Oakridge Holdings LLC", "15000.00", "credit", "OAKRIDGE-A"],
        ])
        patel = BankTransaction.objects.get(bank_reference="PATEL-A")
        self.assertEqual(patel.status, "suggested")
        self.assertEqual(patel.matches.get().line_item.expected_reference, "CC-1003")
        self.assertIn("12,500.00", patel.matches.get().reason)

        oakridge = BankTransaction.objects.get(bank_reference="OAKRIDGE-A")
        self.assertEqual(oakridge.status, "needs_review")
        self.assertEqual(
            set(oakridge.matches.values_list("line_item__expected_reference", flat=True)),
            {"CC-1005", "CC-1006"},
        )
        self.assertTrue(oakridge.review_reason)
        self.assertTrue(all(match.reason for match in oakridge.matches.all()))

    def test_reference_overpayment_needs_review_without_a_proposal(self):
        self.upload([
            ["2026-04-15", "Patel Family Trust CC-1003", "13000.00", "credit", "PATEL-OVER"]
        ])
        payment = BankTransaction.objects.get(bank_reference="PATEL-OVER")
        self.assertEqual(payment.status, "needs_review")
        self.assertFalse(payment.matches.exists())
        self.assertIn("13,000.00", payment.review_reason)
        self.assertIn("12,500.00", payment.review_reason)
