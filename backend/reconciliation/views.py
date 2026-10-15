from django.core.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .organization import get_organization
from .serializers import StatementUploadSerializer
from .services.imports import import_statement

# Create your views here.


class StatementImportView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        organization = get_organization(request)
        serializer = StatementUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            summary = import_statement(organization, serializer.validated_data["file"])
        except ValidationError as error:
            return Response({"detail": "; ".join(error.messages)}, status=400)
        return Response(summary)
