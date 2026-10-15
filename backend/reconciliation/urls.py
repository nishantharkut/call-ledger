from django.urls import path

from .views import (
    ApproveMatchView, IgnoreTransactionView, LineItemListView,
    RejectMatchView, StatementImportView, TransactionListView,
)


urlpatterns = [
    path("imports/", StatementImportView.as_view(), name="statement-import"),
    path("transactions/", TransactionListView.as_view(), name="transaction-list"),
    path("line-items/", LineItemListView.as_view(), name="line-item-list"),
    path("matches/<int:pk>/approve/", ApproveMatchView.as_view(), name="match-approve"),
    path("matches/<int:pk>/reject/", RejectMatchView.as_view(), name="match-reject"),
    path("transactions/<int:pk>/ignore/", IgnoreTransactionView.as_view(), name="transaction-ignore"),
]
