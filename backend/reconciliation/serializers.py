from rest_framework import serializers


class StatementUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
