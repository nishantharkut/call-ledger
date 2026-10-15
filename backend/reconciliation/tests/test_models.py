from datetime import date
from decimal import Decimal
from io import StringIO

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase

from reconciliation import models


class ModelTests(TestCase):
    def setUp(self):
        call_command("seed_demo", stdout=StringIO())
        self.item = models.LineItem.objects.get(expected_reference="CC-1001")
        self.other_item = models.LineItem.objects.get(expected_reference="CC-2001")

    def payment(self, organization=None, **overrides):
        fields = {
            "organization": organization or self.item.organization,
            "date": date(2026, 4, 3),
            "description": "Capital call payment",
            "amount": Decimal("1000.00"),
            "type": "credit",
            "bank_reference": "BANK-001",
        }
        return models.BankTransaction.objects.create(**(fields | overrides))

    def test_funding_status_is_derived_from_amounts(self):
        for funded, status in [
            ("0.00", "open"),
            ("1000.00", "partially_funded"),
            ("27500.00", "funded"),
        ]:
            with self.subTest(funded=funded):
                self.item.amount_funded = Decimal(funded)
                self.assertEqual(self.item.status, status)
                self.assertEqual(
                    self.item.amount_remaining, Decimal("27500.00") - Decimal(funded)
                )

    def test_database_rejects_funding_outside_called_amount(self):
        for funded in [Decimal("-0.01"), Decimal("27500.01")]:
            with self.subTest(funded=funded):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    models.LineItem.objects.filter(pk=self.item.pk).update(
                        amount_funded=funded
                    )
        self.item.refresh_from_db()
        self.assertEqual(self.item.amount_funded, Decimal("0.00"))

    def test_bank_reference_is_unique_within_an_organization(self):
        self.payment()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.payment()
        self.payment(organization=self.other_item.organization)
        self.assertEqual(models.BankTransaction.objects.count(), 2)

    def test_database_rejects_amount_and_type_mismatch(self):
        for amount, payment_type in [
            ("-1.00", "credit"), ("1.00", "debit"), ("0.00", "credit")
        ]:
            with self.subTest(amount=amount, payment_type=payment_type):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    self.payment(amount=Decimal(amount), type=payment_type)

    def test_line_item_validation_rejects_foreign_relationships(self):
        for field in ["capital_call", "investor"]:
            with self.subTest(field=field):
                item = models.LineItem.objects.get(pk=self.item.pk)
                setattr(item, field, getattr(self.other_item, field))
                with self.assertRaises(ValidationError) as error:
                    item.full_clean()
                self.assertIn(field, error.exception.message_dict)

    def test_match_validation_rejects_a_foreign_line_item(self):
        match = models.Match(
            transaction=self.payment(), line_item=self.other_item, reason="Reference found"
        )
        with self.assertRaises(ValidationError) as error:
            match.full_clean()
        self.assertIn("line_item", error.exception.message_dict)

    def test_database_allows_only_one_approved_match_per_transaction(self):
        payment = self.payment()
        models.Match.objects.create(
            transaction=payment, line_item=self.item, status="approved", reason="Reference found"
        )
        other = models.LineItem.objects.get(expected_reference="CC-1002")
        with self.assertRaises(IntegrityError), transaction.atomic():
            models.Match.objects.create(
                transaction=payment, line_item=other, status="approved", reason="Reference found"
            )
