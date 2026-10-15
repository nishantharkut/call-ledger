from django.urls import path

from .views import StatementImportView


urlpatterns = [
    path("imports/", StatementImportView.as_view(), name="statement-import"),
]
