from datetime import date
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from reconciliation import models

# Create your tests here.


class SeedTests(TestCase):
    def seed(self):
        call_command("seed_demo", stdout=StringIO())

    def test_seed_creates_the_required_demo_data(self):
        self.seed()

        self.assertEqual(
            set(models.Organization.objects.values_list("slug", "name")),
            {("northwind", "Northwind Ventures"), ("bluebird", "Bluebird Capital")},
        )
        self.assertEqual(
            set(models.CapitalCall.objects.values_list(
                "organization__slug", "number", "call_date", "due_date"
            )),
            {
                ("northwind", 1, date(2026, 3, 25), date(2026, 4, 10)),
                ("northwind", 2, date(2026, 4, 1), date(2026, 4, 20)),
                ("bluebird", 1, date(2026, 4, 1), date(2026, 4, 15)),
            },
        )
        expected = [
            ("northwind", 1, "Haller Capital LLC", "CC-1001", "27500.00"),
            ("northwind", 1, "Rahul Shah Trust", "CC-1002", "25000.00"),
            ("northwind", 1, "Patel Family Trust", "CC-1003", "12500.00"),
            ("northwind", 1, "Meridian Partners LP", "CC-1004", "15000.00"),
            ("northwind", 1, "Oakridge Holdings LLC", "CC-1005", "15000.00"),
            ("northwind", 2, "Oakridge Holdings LLC", "CC-1006", "15000.00"),
            ("bluebird", 1, "Cedar Grove Fund LP", "CC-2001", "40000.00"),
        ]
        items = models.LineItem.objects.select_related(
            "organization", "capital_call", "investor"
        ).order_by("expected_reference")
        actual = [
            (item.organization.slug, item.capital_call.number, item.investor.name,
             item.expected_reference, str(item.amount_called))
            for item in items
        ]
        self.assertEqual(actual, expected)
        for item in items:
            self.assertEqual(item.amount_funded, Decimal("0.00"))
            self.assertEqual(item.amount_remaining, item.amount_called)
            self.assertEqual(item.status, "open")
            item.full_clean()

    def test_repeated_seed_preserves_records_and_funding(self):
        self.seed()
        item = models.LineItem.objects.get(expected_reference="CC-1001")
        item.amount_funded = Decimal("1000.00")
        item.save(update_fields=["amount_funded"])

        self.seed()

        self.assertEqual(models.Organization.objects.count(), 2)
        self.assertEqual(models.CapitalCall.objects.count(), 3)
        self.assertEqual(models.InvestorEntity.objects.count(), 6)
        self.assertEqual(models.LineItem.objects.count(), 7)
        self.assertEqual(models.BankTransaction.objects.count(), 0)
        self.assertEqual(models.Match.objects.count(), 0)
        item.refresh_from_db()
        self.assertEqual(item.amount_funded, Decimal("1000.00"))
        self.assertEqual(item.amount_remaining, Decimal("26500.00"))
        self.assertEqual(item.status, "partially_funded")
