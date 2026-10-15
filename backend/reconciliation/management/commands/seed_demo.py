from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from reconciliation.models import CapitalCall, InvestorEntity, LineItem, Organization


class Command(BaseCommand):
    help = "Create the two demo organizations and their capital call line items."

    @transaction.atomic
    def handle(self, *args, **options):
        organizations = {}
        for slug, name in [
            ("northwind", "Northwind Ventures"),
            ("bluebird", "Bluebird Capital"),
        ]:
            organizations[slug], _ = Organization.objects.get_or_create(
                slug=slug, defaults={"name": name}
            )

        calls = {}
        for slug, number, call_date, due_date in [
            ("northwind", 1, date(2026, 3, 25), date(2026, 4, 10)),
            ("northwind", 2, date(2026, 4, 1), date(2026, 4, 20)),
            ("bluebird", 1, date(2026, 4, 1), date(2026, 4, 15)),
        ]:
            calls[slug, number], _ = CapitalCall.objects.get_or_create(
                organization=organizations[slug], number=number,
                defaults={"call_date": call_date, "due_date": due_date},
            )

        created_count = 0
        for slug, call_number, name, reference, amount in [
            ("northwind", 1, "Haller Capital LLC", "CC-1001", "27500.00"),
            ("northwind", 1, "Rahul Shah Trust", "CC-1002", "25000.00"),
            ("northwind", 1, "Patel Family Trust", "CC-1003", "12500.00"),
            ("northwind", 1, "Meridian Partners LP", "CC-1004", "15000.00"),
            ("northwind", 1, "Oakridge Holdings LLC", "CC-1005", "15000.00"),
            ("northwind", 2, "Oakridge Holdings LLC", "CC-1006", "15000.00"),
            ("bluebird", 1, "Cedar Grove Fund LP", "CC-2001", "40000.00"),
        ]:
            organization = organizations[slug]
            investor, _ = InvestorEntity.objects.get_or_create(
                organization=organization, name=name
            )
            # Defaults apply only on creation, so re-seeding preserves funding.
            item, created = LineItem.objects.get_or_create(
                organization=organization, expected_reference=reference,
                defaults={
                    "capital_call": calls[slug, call_number],
                    "investor": investor,
                    "amount_called": Decimal(amount),
                },
            )
            item.full_clean()
            created_count += int(created)

        self.stdout.write(f"Created {created_count} demo line items.")
