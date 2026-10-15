import logging

from reconciliation.models import BankTransaction

from .airtable import AirtableClient, AirtableError


logger = logging.getLogger(__name__)
BATCH_SIZE = 10


def transaction_fields(payment, organization):
    return {
        "Transaction ID": str(payment.id),
        "Bank reference": payment.bank_reference,
        "Organization": organization.slug,
        "Date": payment.date.isoformat(),
        "Description": payment.description,
        # The Airtable field is text so decimal precision is preserved.
        "Amount (USD)": format(payment.amount, ".2f"),
        "Status": payment.status,
        "Review reason": payment.review_reason,
    }


def created_record_ids(batch, records):
    expected = {str(payment.id) for payment in batch}
    record_ids = {}

    for record in records:
        payment_id = record.get("fields", {}).get("Transaction ID")
        record_id = record.get("id")
        if (
            payment_id not in expected
            or payment_id in record_ids
            or not isinstance(record_id, str)
            or not record_id
            or len(record_id) > 255
        ):
            raise AirtableError("Airtable returned invalid record identifiers.")
        record_ids[payment_id] = record_id

    if record_ids.keys() != expected or len(set(record_ids.values())) != len(batch):
        raise AirtableError("Airtable did not confirm every created record.")

    return record_ids


def sync_review_transactions(organization, payment_ids, client=None):
    payments = list(BankTransaction.objects.filter(
        organization=organization,
        pk__in=payment_ids,
        status=BankTransaction.Status.NEEDS_REVIEW,
        airtable_sync_status=BankTransaction.SyncStatus.NOT_SYNCED,
        airtable_record_id="",
    ).order_by("id"))
    if not payments:
        return

    try:
        client = client if client is not None else AirtableClient.from_settings()
        if client is None:
            return

        for start in range(0, len(payments), BATCH_SIZE):
            batch = payments[start:start + BATCH_SIZE]
            fields = [transaction_fields(payment, organization) for payment in batch]
            records = client.create_records(fields)

            # Match by local ID rather than assuming the response preserves row order.
            record_ids = created_record_ids(batch, records)
            for payment in batch:
                payment.airtable_record_id = record_ids[str(payment.id)]
                payment.airtable_sync_status = BankTransaction.SyncStatus.SYNCED

            BankTransaction.objects.bulk_update(
                batch, ["airtable_record_id", "airtable_sync_status"]
            )
    except Exception as error:
        # This optional integration must not turn a committed import into a failed upload.
        # Check saved status because assigning an ID in memory does not mean it was stored.
        BankTransaction.objects.filter(
            organization=organization,
            pk__in=[payment.id for payment in payments],
            airtable_sync_status=BankTransaction.SyncStatus.NOT_SYNCED,
        ).update(airtable_sync_status=BankTransaction.SyncStatus.SYNC_FAILED)

        # Stop on the first failure rather than repeatedly calling an unavailable service.
        logger.warning(
            "Airtable sync stopped for organization %s: %s",
            organization.slug,
            str(error) if isinstance(error, AirtableError) else type(error).__name__,
        )
