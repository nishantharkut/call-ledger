from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .organization import get_organization
from .models import BankTransaction
from .queries import line_items_for, matches_for
from .serializers import BankTransactionSerializer, LineItemSerializer, StatementUploadSerializer
from .services.actions import approve_match, ignore_transaction, reject_match
from .services.imports import import_statement

# Create your views here.


class OrganizationMixin:
    authentication_classes = []
    permission_classes = [AllowAny]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.organization = get_organization(request)


class StatementImportView(OrganizationMixin, APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = StatementUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            summary = import_statement(self.organization, serializer.validated_data["file"])
        except ValidationError as error:
            return Response({"detail": "; ".join(error.messages)}, status=400)
        return Response(summary)


class TransactionPagination(PageNumberPagination):
    page_size = 50


class TransactionListView(OrganizationMixin, ListAPIView):
    serializer_class = BankTransactionSerializer
    pagination_class = TransactionPagination

    def get_queryset(self):
        # Fetch nested candidates together instead of issuing queries for each table row.
        matches = matches_for(self.organization).select_related(
            "line_item__organization", "line_item__investor", "line_item__capital_call",
        ).order_by("id")
        return BankTransaction.objects.filter(organization=self.organization).order_by(
            "-date", "-id",
        ).prefetch_related(Prefetch("matches", queryset=matches))


class LineItemListView(OrganizationMixin, ListAPIView):
    serializer_class = LineItemSerializer
    pagination_class = None

    def get_queryset(self):
        return line_items_for(self.organization).select_related(
            "organization", "investor", "capital_call",
        ).order_by("capital_call__number", "id")


class ApproveMatchView(OrganizationMixin, APIView):
    def post(self, request, pk):
        payment = approve_match(self.organization, pk)
        return Response({"transaction_id": payment.pk, "status": payment.status})


class RejectMatchView(OrganizationMixin, APIView):
    def post(self, request, pk):
        payment = reject_match(self.organization, pk)
        return Response({"transaction_id": payment.pk, "status": payment.status})


class IgnoreTransactionView(OrganizationMixin, APIView):
    def post(self, request, pk):
        payment = ignore_transaction(self.organization, pk)
        return Response({"transaction_id": payment.pk, "status": payment.status})
