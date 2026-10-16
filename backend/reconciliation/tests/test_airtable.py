from io import StringIO
from unittest.mock import Mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import connection
from django.test import TransactionTestCase, override_settings

from reconciliation.models import BankTransaction, Organization
from reconciliation.services.imports import import_statement


@override_settings(AIRTABLE_PAT="", AIRTABLE_BASE_ID="", AIRTABLE_TABLE_NAME="")
class AirtableTests(TransactionTestCase):
    def setUp(self):
        call_command("seed_demo", stdout=StringIO())
        self.organization = Organization.objects.get(slug="northwind")

    def statement(self):
        return SimpleUploadedFile("review.csv", (
            "date,description,amount,type,reference\n"
            "2026-04-07,Unknown wire,9999.99,credit,REVIEW\n"
            "2026-04-07,Reference CC1003,12500.00,credit,PROPOSAL\n"
            "2026-04-07,Bank fee,-25.00,debit,FEE\n"
        ).encode())

    def test_only_review_transactions_are_created_and_record_ids_are_saved(self):
        def create_records(fields):
            self.assertFalse(connection.in_atomic_block)
            return [{"id": f"rec{row['Transaction ID']}", "fields": row} for row in fields]

        client = Mock()
        client.create_records.side_effect = create_records

        result = import_statement(self.organization, self.statement(), airtable_client=client)

        self.assertEqual(result["imported"], 3)
        client.create_records.assert_called_once()
        fields = client.create_records.call_args.args[0]
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0]["Bank reference"], "REVIEW")
        self.assertEqual(fields[0]["Amount (USD)"], "9999.99")
        payment = BankTransaction.objects.get(bank_reference="REVIEW")
        self.assertEqual(payment.airtable_record_id, f"rec{payment.pk}")
        self.assertEqual(payment.airtable_sync_status, "synced")
        self.assertFalse(BankTransaction.objects.exclude(pk=payment.pk).exclude(
            airtable_sync_status="not_synced",
        ).exists())

        repeated = import_statement(self.organization, self.statement(), airtable_client=client)
        self.assertEqual(repeated["duplicates"], 3)
        client.create_records.assert_called_once()

    def test_airtable_failure_preserves_the_import_and_records_sync_failure(self):
        client = Mock()
        client.create_records.side_effect = RuntimeError("Airtable unavailable")

        with self.assertLogs("reconciliation.services.airtable_sync", level="WARNING"):
            result = import_statement(self.organization, self.statement(), airtable_client=client)

        self.assertEqual(result["imported"], 3)
        self.assertEqual(BankTransaction.objects.count(), 3)
        payment = BankTransaction.objects.get(bank_reference="REVIEW")
        self.assertEqual(payment.airtable_record_id, "")
        self.assertEqual(payment.airtable_sync_status, "sync_failed")
        proposal = BankTransaction.objects.get(bank_reference="PROPOSAL")
        self.assertEqual(proposal.status, "suggested")
