import re

from django.db.models import F

from reconciliation.models import BankTransaction, LineItem, Match


def normalize_reference(value):
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def normalize_words(value):
    return " ".join(re.sub(r"[^A-Z0-9]", " ", value.upper()).split())


def normalize_name(value):
    words = normalize_words(value).split()
    # Strip one legal suffix and keep TRUST as part of the name.
    if words and words[-1] in {"LLC", "LP", "LTD", "INC"}:
        words.pop()
    return " ".join(words)


def reference_reason(line_item, amount):
    remaining = line_item.amount_remaining
    if amount == remaining:
        detail = f"amount equals remaining {remaining:,.2f}"
    elif amount < remaining:
        detail = f"partial payment {amount:,.2f} of remaining {remaining:,.2f}"
    else:
        detail = f"amount {amount:,.2f} exceeds remaining {remaining:,.2f}"
    return f"Reference {line_item.expected_reference} found; {detail}."


def match_payment(payment, line_items):
    # Only consider calls issued on or before the payment date.
    eligible = [
        item for item in line_items
        if item.capital_call.call_date <= payment.date
    ]
    description = normalize_reference(payment.description)
    bank_reference = normalize_reference(payment.bank_reference)
    reference_hits = []
    for item in eligible:
        reference = normalize_reference(item.expected_reference)
        # Search fields separately so their boundary cannot form a false reference.
        if reference and (reference in description or reference in bank_reference):
            reference_hits.append(item)

    if reference_hits:
        # Any reference hit takes precedence, including ambiguous hits and overpayments.
        if len(reference_hits) == 1 and payment.amount > reference_hits[0].amount_remaining:
            payment.review_reason = reference_reason(reference_hits[0], payment.amount)
            return []
        candidates = reference_hits
        reasons = [reference_reason(item, payment.amount) for item in candidates]
        review_reason = f"{len(candidates)} eligible wire references found; choose a line item."
    else:
        # Space padding enforces whole-word names without requiring a full description match.
        description_words = f" {normalize_words(payment.description)} "
        candidates = []
        for item in eligible:
            name = normalize_name(item.investor.name)
            if (name and f" {name} " in description_words
                    and payment.amount == item.amount_remaining):
                candidates.append(item)
        reasons = [
            f"Investor name {item.investor.name} found; "
            f"amount equals remaining {item.amount_remaining:,.2f}."
            for item in candidates
        ]
        review_reason = f"{len(candidates)} investor name and amount matches found; choose a line item."

    if len(candidates) == 1:
        payment.status = BankTransaction.Status.SUGGESTED
        payment.review_reason = ""
    elif candidates:
        payment.review_reason = review_reason
    else:
        payment.review_reason = (
            "No eligible reference or investor name with matching remaining amount was found."
        )
    return [
        Match(transaction=payment, line_item=item, reason=reason)
        for item, reason in zip(candidates, reasons)
    ]


def match_transactions(organization, transactions):
    credits = [payment for payment in transactions if payment.type == BankTransaction.Type.CREDIT]
    if not credits:
        return

    # Load candidates and their related records once for the entire upload.
    line_items = list(LineItem.objects.filter(
        organization=organization,
        capital_call__organization=organization,
        investor__organization=organization,
        amount_funded__lt=F("amount_called"),
    ).select_related("capital_call", "investor").order_by("id"))

    matches = []
    for payment in credits:
        # Suggestions leave funding unchanged. Approval checks the remaining amount again.
        matches.extend(match_payment(payment, line_items))
    Match.objects.bulk_create(matches, batch_size=500)
    BankTransaction.objects.bulk_update(credits, ["status", "review_reason"], batch_size=500)
