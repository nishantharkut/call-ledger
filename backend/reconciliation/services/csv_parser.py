import csv
import re
from datetime import date
from decimal import Decimal
from io import StringIO

from django.core.exceptions import ValidationError

from reconciliation.models import BankTransaction


REQUIRED_COLUMNS = ("date", "description", "amount", "type", "reference")
MAX_STATEMENT_BYTES = 10 * 1024 * 1024
# Allow any field that fits within the bounded upload.
csv.field_size_limit(MAX_STATEMENT_BYTES)
AMOUNT_PATTERN = re.compile(
    r"[+-]?(?:(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]*)?|\.[0-9]+)"
)


def parse_row(values):
    if any("\x00" in values[column] for column in REQUIRED_COLUMNS):
        raise ValidationError("Fields cannot contain null characters.")
    try:
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", values["date"]):
            raise ValueError
        payment_date = date.fromisoformat(values["date"])
    except ValueError as error:
        raise ValidationError("Date must be a real calendar date in YYYY-MM-DD format.") from error

    if not values["description"]:
        raise ValidationError("Description is required.")
    if not values["reference"]:
        raise ValidationError("Reference is required.")
    BankTransaction._meta.get_field("bank_reference").run_validators(values["reference"])

    payment_type = values["type"].lower()
    if payment_type not in BankTransaction.Type.values:
        raise ValidationError("Type must be credit or debit.")
    if not AMOUNT_PATTERN.fullmatch(values["amount"]):
        raise ValidationError("Amount must be a decimal number with valid thousands separators.")
    amount = Decimal(values["amount"].replace(",", ""))
    BankTransaction._meta.get_field("amount").run_validators(amount)
    if amount == 0:
        raise ValidationError("Amount cannot be zero.")
    if payment_type == BankTransaction.Type.CREDIT and amount < 0:
        raise ValidationError("Credit amount must be positive.")
    if payment_type == BankTransaction.Type.DEBIT and amount > 0:
        raise ValidationError("Debit amount must be negative.")

    return {
        "date": payment_date,
        "description": values["description"],
        "amount": amount,
        "type": payment_type,
        "bank_reference": values["reference"],
    }


def read_statement(upload):
    content = upload.read(MAX_STATEMENT_BYTES + 1)
    if len(content) > MAX_STATEMENT_BYTES:
        raise ValidationError("Statement must be 10 MB or smaller.")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValidationError("Statement must use UTF-8 encoding.") from error

    reader = csv.reader(StringIO(text, newline=""), strict=True)
    try:
        columns = [column.strip() for column in next(reader, [])]
    except csv.Error as error:
        raise ValidationError("CSV header is malformed.") from error
    missing = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing:
        raise ValidationError(f"Missing required columns: {', '.join(missing)}.")
    if len(set(columns)) != len(columns) or any(not column for column in columns):
        raise ValidationError("Column names must be nonempty and unique.")

    rows, errors = [], []
    while True:
        # Report the record's starting line even when a quoted field spans lines.
        line = reader.line_num + 1
        try:
            fields = next(reader)
        except StopIteration:
            break
        except csv.Error as error:
            errors.append({"line": line, "message": f"Malformed CSV row: {error}."})
            continue
        if not fields or (len(fields) == 1 and not fields[0].strip()):
            continue
        if len(fields) != len(columns):
            errors.append({"line": line, "message": "Row does not match the number of columns."})
            continue
        values = dict(zip(columns, (field.strip() for field in fields)))
        try:
            rows.append((line, parse_row(values)))
        except ValidationError as error:
            errors.append({"line": line, "message": "; ".join(error.messages)})
    return rows, errors
