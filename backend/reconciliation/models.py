from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

# Create your models here.


class Organization(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class InvestorEntity(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="investors"
    )
    name = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"], name="unique_investor_per_org"
            ),
        ]

    def __str__(self):
        return self.name


class CapitalCall(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="capital_calls"
    )
    number = models.PositiveIntegerField()
    call_date = models.DateField()
    due_date = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "number"], name="unique_call_number_per_org"
            ),
        ]

    def __str__(self):
        return f"{self.organization.slug} call #{self.number}"


class LineItem(models.Model):
    # Filter tenants directly. clean() checks that related records share the tenant.
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="line_items"
    )
    capital_call = models.ForeignKey(
        CapitalCall, on_delete=models.PROTECT, related_name="line_items"
    )
    investor = models.ForeignKey(
        InvestorEntity, on_delete=models.PROTECT, related_name="line_items"
    )
    expected_reference = models.CharField(max_length=64)
    amount_called = models.DecimalField(max_digits=18, decimal_places=2)
    amount_funded = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0.00")
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "expected_reference"], name="unique_wire_reference_per_org"
            ),
            models.UniqueConstraint(
                fields=["capital_call", "investor"], name="unique_investor_per_call"
            ),
            models.CheckConstraint(
                condition=models.Q(
                    amount_called__gt=0,
                    amount_funded__gte=0,
                    amount_funded__lte=models.F("amount_called"),
                ),
                name="line_item_funding_within_called",
            ),
        ]

    @property
    def amount_remaining(self):
        return self.amount_called - self.amount_funded

    @property
    def status(self):
        if self.amount_remaining == 0:
            return "funded"
        if self.amount_funded > 0:
            return "partially_funded"
        return "open"

    def clean(self):
        errors = {}
        if self.capital_call_id and self.capital_call.organization_id != self.organization_id:
            errors["capital_call"] = "Capital call must belong to the same organization."
        if self.investor_id and self.investor.organization_id != self.organization_id:
            errors["investor"] = "Investor must belong to the same organization."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.expected_reference


class BankTransaction(models.Model):
    class Type(models.TextChoices):
        CREDIT = "credit", "Credit"
        DEBIT = "debit", "Debit"

    class Status(models.TextChoices):
        SUGGESTED = "suggested", "Suggested"
        NEEDS_REVIEW = "needs_review", "Needs review"
        RECONCILED = "reconciled", "Reconciled"
        IGNORED = "ignored", "Ignored"

    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="transactions"
    )
    date = models.DateField()
    description = models.TextField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    type = models.CharField(max_length=6, choices=Type.choices)
    bank_reference = models.CharField(max_length=255)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.NEEDS_REVIEW
    )
    review_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [
            models.Index(fields=["organization", "-date", "-id"], name="transaction_org_date_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "bank_reference"], name="unique_bank_reference_per_org"
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(type="credit", amount__gt=0)
                    | models.Q(type="debit", amount__lt=0)
                ),
                name="transaction_sign_matches_type",
            ),
        ]

    def __str__(self):
        return self.bank_reference


class Match(models.Model):
    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposed"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    transaction = models.ForeignKey(
        BankTransaction, on_delete=models.PROTECT, related_name="matches"
    )
    line_item = models.ForeignKey(
        LineItem, on_delete=models.PROTECT, related_name="matches"
    )
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PROPOSED)
    reason = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["transaction", "line_item"], name="unique_transaction_line_item_match"
            ),
            models.UniqueConstraint(
                fields=["transaction"], condition=models.Q(status="approved"),
                name="one_approved_match_per_transaction",
            ),
        ]

    def clean(self):
        if self.transaction_id and self.line_item_id:
            if self.transaction.organization_id != self.line_item.organization_id:
                raise ValidationError({
                    "line_item": "Line item must belong to the transaction's organization."
                })
