import csv
from decimal import Decimal
from io import StringIO
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from rest_framework.test import APITestCase

from reconciliation.models import BankTransaction, LineItem, Organization


class ImportTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())

    def statement(self, rows, columns=None):
        output = StringIO()
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(columns or ["date", "description", "amount", "type", "reference"])
        writer.writerows(rows)
        return output.getvalue()

    def upload(self, content, organization="northwind"):
        if isinstance(content, str):
            content = content.encode("utf-8")
        file = SimpleUploadedFile("statement.csv", content, content_type="text/csv")
        headers = {} if organization is None else {"HTTP_X_ORGANIZATION": organization}
        return self.client.post("/api/imports/", {"file": file}, format="multipart", **headers)

    def test_missing_columns_reject_the_file_without_writes(self):
        columns = ["date", "description", "amount", "type", "reference"]
        for missing in columns:
            with self.subTest(missing=missing):
                content = self.statement([], [column for column in columns if column != missing])
                response = self.upload(content)
                self.assertEqual(response.status_code, 400)
                self.assertIn(missing, response.data["detail"])
                self.assertEqual(BankTransaction.objects.count(), 0)

    def test_fields_are_trimmed_and_money_is_stored_as_decimal(self):
        response = self.upload(self.statement([
            [" 2026-04-03 ", " Incoming wire ", " 25,000.00 ", " CREDIT ", " BANK-1 "],
            ["2026-04-04", " Bank fee ", "-25.00", "DeBiT", "BANK-2"],
        ]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["imported"], 2)
        self.assertEqual(response.data["errors"], [])
        credit = BankTransaction.objects.get(bank_reference="BANK-1")
        debit = BankTransaction.objects.get(bank_reference="BANK-2")
        self.assertIsInstance(credit.amount, Decimal)
        self.assertEqual(credit.amount, Decimal("25000.00"))
        self.assertEqual(credit.description, "Incoming wire")
        self.assertEqual(credit.type, "credit")
        self.assertEqual(debit.amount, Decimal("-25.00"))
        self.assertEqual(debit.status, "ignored")

    def test_invalid_rows_are_reported_and_valid_rows_still_import(self):
        invalid = [
            {"date": "2026-04-31"}, {"date": "20260403"},
            {"amount": "0"}, {"amount": "-1.00"},
            {"amount": "1.00", "type": "debit"},
            {"amount": "NaN"}, {"amount": "Infinity"},
            {"amount": "12,34.00"}, {"amount": "1.001"},
            {"amount": "10000000000000000.00"}, {"amount": "1_000.00"},
            {"description": "   "}, {"reference": "   "},
            {"type": "refund"}, {"reference": "X" * 256},
            {"description": "Payment\x00reference"},
        ]
        rows = []
        for index, overrides in enumerate(invalid):
            row = dict(date="2026-04-03", description="Payment", amount="10.00",
                       type="credit", reference=f"BAD-{index}")
            rows.append(list((row | overrides).values()))
        rows.append(["2026-04-03", "Valid payment", "100.00", "credit", "VALID"])

        response = self.upload(self.statement(rows))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["imported"], 1)
        self.assertEqual(response.data["duplicates"], 0)
        self.assertEqual(
            [error["line"] for error in response.data["errors"]],
            list(range(2, len(invalid) + 2)),
        )
        self.assertTrue(all(error["message"] for error in response.data["errors"]))
        self.assertEqual(BankTransaction.objects.get().bank_reference, "VALID")

    def test_duplicates_within_file_and_on_reupload_are_reported(self):
        content = self.statement([
            ["2026-04-03", "Payment", "100.00", "credit", "BANK-A"],
            ["2026-04-03", "Payment", "100.00", "credit", " BANK-A "],
            ["2026-04-04", "Payment", "50.00", "credit", "BANK-B"],
        ])
        first = self.upload(content)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["imported"], 2)
        self.assertEqual(first.data["duplicates"], 1)
        self.assertEqual(first.data["duplicate_rows"], [{"line": 3, "reference": "BANK-A"}])

        second = self.upload(content)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data["imported"], 0)
        self.assertEqual(second.data["duplicates"], 3)
        self.assertEqual(BankTransaction.objects.count(), 2)

    def test_organization_header_is_required_and_must_exist(self):
        content = self.statement([["2026-04-03", "Payment", "100.00", "credit", "BANK-A"]])
        for organization, status in [(None, 400), (" ", 400), ("unknown", 404)]:
            with self.subTest(organization=organization):
                response = self.upload(content, organization)
                self.assertEqual(response.status_code, status)
                self.assertIn("detail", response.data)
        self.assertEqual(BankTransaction.objects.count(), 0)

    def test_two_organizations_can_import_the_same_bank_reference(self):
        content = self.statement([["2026-04-03", "Payment", "100.00", "credit", "BANK-A"]])
        for organization in ["northwind", "bluebird"]:
            response = self.upload(content, organization)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["imported"], 1)
            self.assertEqual(response.data["duplicates"], 0)
            self.assertEqual(BankTransaction.objects.filter(
                organization=Organization.objects.get(slug=organization)
            ).count(), 1)

    def test_original_sample_summary_uses_physical_line_numbers(self):
        sample = Path(__file__).resolve().parents[3] / "sample_bank_statement.csv"
        response = self.upload(sample.read_bytes())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["imported"], 11)
        self.assertEqual(response.data["duplicates"], 1)
        self.assertEqual(response.data["duplicate_rows"][0]["line"], 11)
        self.assertEqual([error["line"] for error in response.data["errors"]], [13, 14])
        self.assertEqual(BankTransaction.objects.filter(type="debit", status="ignored").count(), 1)
        self.assertFalse(LineItem.objects.exclude(amount_funded=Decimal("0.00")).exists())

    def test_multiline_fields_and_blank_lines_keep_correct_error_locations(self):
        content = (
            'date,description,amount,type,reference\n'
            '2026-04-03,"Payment\nfor capital",100.00,credit,MULTI\n'
            '2026-04-03,missing fields\n'
            '2026-04-03,too many,100.00,credit,EXTRA,unexpected\n'
            '\n2026-04-04,Next payment,50.00,credit,NEXT\n'
        )
        response = self.upload(content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["imported"], 2)
        self.assertEqual([error["line"] for error in response.data["errors"]], [4, 5])
        self.assertEqual(BankTransaction.objects.get(bank_reference="MULTI").description,
                         "Payment\nfor capital")

    def test_invalid_files_are_rejected_without_writes(self):
        for content in [b"", b"\xff", b"date,date,amount,type,reference\n", b'"date,description\n']:
            with self.subTest(content=content):
                response = self.upload(content)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(BankTransaction.objects.count(), 0)
        response = self.client.post("/api/imports/", {}, format="multipart",
                                    HTTP_X_ORGANIZATION="northwind")
        self.assertEqual(response.status_code, 400)

    def test_bom_reordered_headers_and_extra_columns_are_supported(self):
        content = (
            '\ufeff reference ,type,amount,description,date,unused\n'
            ' BOM-1 ,credit,0.50,Payment,2026-04-03,anything\n'
        )
        response = self.upload(content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["imported"], 1)
        self.assertEqual(BankTransaction.objects.get().amount, Decimal("0.50"))

    def test_long_description_within_upload_limit_is_preserved(self):
        description = "Wire payment " * 12000
        content = self.statement([
            ["2026-04-03", description, "100.00", "credit", "LONG-DESCRIPTION"]
        ])
        response = self.upload(content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["imported"], 1)
        self.assertEqual(response.data["errors"], [])
        self.assertEqual(BankTransaction.objects.get().description, description.strip())
