from .models import LineItem, Match


def line_items_for(organization):
    # Check related tenants too because model clean() is not called by every write.
    return LineItem.objects.filter(
        organization=organization,
        capital_call__organization=organization,
        investor__organization=organization,
    )


def matches_for(organization):
    return Match.objects.filter(
        transaction__organization=organization,
        line_item__organization=organization,
        line_item__capital_call__organization=organization,
        line_item__investor__organization=organization,
    )
