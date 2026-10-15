from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from .models import Organization


def get_organization(request):
    slug = request.headers.get("X-Organization", "").strip()
    if not slug:
        raise ValidationError({"detail": "X-Organization header is required."})
    return get_object_or_404(Organization, slug=slug)
