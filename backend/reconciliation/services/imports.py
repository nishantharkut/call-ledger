from django.db import transaction

from reconciliation.models import BankTransaction, Organization

from .csv_parser import read_statement
from .matching import match_transactions


def import_statement(organization, upload):
    rows, errors = read_statement(upload)
    references = {values["bank_reference"] for _, values in rows}
    transactions = []
    duplicates = []

    with transaction.atomic():
        # Serialize tenant uploads so bulk inserts can report exact duplicate counts.
        organization = Organization.objects.select_for_update().get(pk=organization.pk)
        existing = set(BankTransaction.objects.filter(
            organization=organization, bank_reference__in=references
        ).values_list("bank_reference", flat=True))

        for line, values in rows:
            reference = values["bank_reference"]
            if reference in existing:
                duplicates.append({"line": line, "reference": reference})
                continue

            is_debit = values["type"] == BankTransaction.Type.DEBIT
            status = (BankTransaction.Status.IGNORED if is_debit
                      else BankTransaction.Status.NEEDS_REVIEW)
            transactions.append(BankTransaction(
                organization=organization, **values, status=status,
            ))
            # Include accepted rows immediately to catch duplicates within this file.
            existing.add(reference)
        BankTransaction.objects.bulk_create(transactions, batch_size=500)
        # Save matches using the new row IDs within this transaction.
        match_transactions(organization, transactions)

    return {
        "imported": len(transactions),
        "duplicates": len(duplicates),
        "duplicate_rows": duplicates,
        "errors": errors,
    }
