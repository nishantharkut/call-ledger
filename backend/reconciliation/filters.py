from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend

from .models import BankTransaction


class TransactionFilter(BaseFilterBackend):
    ordering_fields = {
        "-date": ("-date", "-id"),
        "date": ("date", "id"),
        "-amount": ("-amount", "-date", "-id"),
        "amount": ("amount", "-date", "-id"),
    }

    def filter_queryset(self, request, queryset, view):
        status = request.query_params.get("status", "").strip()
        ordering = request.query_params.get("ordering", "-date").strip()

        if status and status not in BankTransaction.Status.values:
            raise ValidationError({"status": "Choose a valid transaction status."})
        if ordering not in self.ordering_fields:
            raise ValidationError({"ordering": "Choose date, -date, amount, or -amount."})

        if status:
            queryset = queryset.filter(status=status)

        # A unique tie-breaker keeps equal dates and amounts stable across pages.
        return queryset.order_by(*self.ordering_fields[ordering])
