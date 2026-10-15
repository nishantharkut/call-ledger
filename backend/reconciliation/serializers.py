from rest_framework import serializers

from .models import BankTransaction, LineItem, Match


class StatementUploadSerializer(serializers.Serializer):
    file = serializers.FileField()


class LineItemSerializer(serializers.ModelSerializer):
    organization = serializers.CharField(source="organization.slug")
    investor_name = serializers.CharField(source="investor.name")
    call_number = serializers.IntegerField(source="capital_call.number")
    call_date = serializers.DateField(source="capital_call.call_date")
    due_date = serializers.DateField(source="capital_call.due_date")
    amount_remaining = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = LineItem
        fields = [
            "id", "organization", "investor_name", "call_number", "call_date", "due_date",
            "expected_reference", "amount_called", "amount_funded", "amount_remaining", "status",
        ]


class MatchSerializer(serializers.ModelSerializer):
    line_item = LineItemSerializer(read_only=True)

    class Meta:
        model = Match
        fields = ["id", "status", "reason", "line_item"]


class BankTransactionSerializer(serializers.ModelSerializer):
    matches = MatchSerializer(many=True, read_only=True)

    class Meta:
        model = BankTransaction
        fields = [
            "id", "date", "description", "amount", "type", "bank_reference",
            "status", "review_reason", "matches",
        ]
