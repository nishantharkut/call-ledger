from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import APIException

from reconciliation.models import BankTransaction, Match
from reconciliation.queries import line_items_for, matches_for


class Conflict(APIException):
    status_code = 409
    default_detail = "The transaction can no longer accept this action."
    default_code = "conflict"


def lock_payment(organization, payment_id):
    return get_object_or_404(
        BankTransaction.objects.select_for_update().filter(organization=organization),
        pk=payment_id,
    )


def require_active_credit(payment):
    if payment.type != BankTransaction.Type.CREDIT or payment.status not in {
        BankTransaction.Status.SUGGESTED, BankTransaction.Status.NEEDS_REVIEW,
    }:
        raise Conflict()


def lock_proposal(organization, match_id):
    match = get_object_or_404(matches_for(organization), pk=match_id)
    # All actions lock the payment first so its matches cannot change during an action.
    payment = lock_payment(organization, match.transaction_id)
    require_active_credit(payment)
    # Another request may have changed the proposal while this request waited for the lock.
    match = get_object_or_404(matches_for(organization), pk=match_id)
    if match.status != Match.Status.PROPOSED:
        raise Conflict("Only proposed matches can be approved or rejected.")
    return payment, match


@transaction.atomic
def approve_match(organization, match_id):
    payment, match = lock_proposal(organization, match_id)
    # Different payments can target this balance. Lock it before checking the amount.
    item = get_object_or_404(
        line_items_for(organization).select_for_update(of=("self",)),
        pk=match.line_item_id,
    )
    if payment.amount > item.amount_remaining:
        raise Conflict("Payment exceeds the line item's current remaining amount.")

    item.amount_funded += payment.amount
    item.save(update_fields=["amount_funded"])
    match.status = Match.Status.APPROVED
    match.save(update_fields=["status"])
    matches_for(organization).filter(transaction=payment).exclude(pk=match.pk).update(
        status=Match.Status.REJECTED,
    )
    payment.status = BankTransaction.Status.RECONCILED
    payment.review_reason = ""
    payment.save(update_fields=["status", "review_reason"])
    return payment


@transaction.atomic
def reject_match(organization, match_id):
    payment, match = lock_proposal(organization, match_id)
    match.status = Match.Status.REJECTED
    match.save(update_fields=["status"])
    if not matches_for(organization).filter(
        transaction=payment, status=Match.Status.PROPOSED,
    ).exists():
        payment.status = BankTransaction.Status.NEEDS_REVIEW
        payment.review_reason = "All proposed matches were rejected."
        payment.save(update_fields=["status", "review_reason"])
    return payment


@transaction.atomic
def ignore_transaction(organization, payment_id):
    payment = lock_payment(organization, payment_id)
    require_active_credit(payment)
    matches_for(organization).filter(transaction=payment).update(status=Match.Status.REJECTED)
    payment.status = BankTransaction.Status.IGNORED
    payment.review_reason = ""
    payment.save(update_fields=["status", "review_reason"])
    return payment
