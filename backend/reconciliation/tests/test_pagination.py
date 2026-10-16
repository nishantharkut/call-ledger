from datetime import date, timedelta
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from rest_framework.test import APITestCase

from reconciliation.models import BankTransaction, Organization


class PaginationTests(APITestCase):
    def test_pages_preserve_order_without_missing_or_repeating_transactions(self):
        call_command("seed_demo", stdout=StringIO())
        organization = Organization.objects.get(slug="northwind")
        BankTransaction.objects.bulk_create([
            BankTransaction(
                organization=organization, date=date(2026, 4, 1) + timedelta(days=index % 3),
                description="Incoming wire", amount=Decimal("100.00"),
                type="credit", bank_reference=f"PAGE-{index}",
            )
            for index in range(53)
        ])
        expected = list(BankTransaction.objects.filter(organization=organization).order_by(
            "-date", "-id",
        ).values_list("id", flat=True))

        first = self.client.get("/api/transactions/", HTTP_X_ORGANIZATION="northwind")
        second = self.client.get("/api/transactions/?page=2", HTTP_X_ORGANIZATION="northwind")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data["count"], 53)
        self.assertEqual(len(first.data["results"]), 50)
        self.assertEqual(len(second.data["results"]), 3)
        self.assertIsNone(first.data["previous"])
        self.assertIsNotNone(first.data["next"])
        self.assertIsNotNone(second.data["previous"])
        self.assertIsNone(second.data["next"])
        observed = [row["id"] for row in first.data["results"] + second.data["results"]]
        self.assertEqual(observed, expected)

        invalid = self.client.get("/api/transactions/?page=3", HTTP_X_ORGANIZATION="northwind")
        self.assertEqual(invalid.status_code, 404)
