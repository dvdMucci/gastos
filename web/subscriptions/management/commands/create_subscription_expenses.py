from django.core.management.base import BaseCommand
from subscriptions.models import Subscription


class Command(BaseCommand):
    help = (
        'Extiende el horizonte de gastos de suscripciones activas y '
        'actualiza/fija cotización USD (estimado hasta el día de pago).'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--months-ahead',
            type=int,
            default=Subscription.EXPENSE_HORIZON_MONTHS,
            help=f'Meses de horizonte a materializar (default: {Subscription.EXPENSE_HORIZON_MONTHS})',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se haría sin crear los gastos',
        )

    def handle(self, *args, **options):
        months_ahead = options['months_ahead']
        dry_run = options['dry_run']

        self.stdout.write(
            f'Extendiendo horizonte de suscripciones activas '
            f'({months_ahead} meses adelante)...'
        )

        if dry_run:
            qs = Subscription.objects.filter(status='active', auto_create_expense=True)
            count = sum(1 for sub in qs if sub.is_active())
            self.stdout.write(
                self.style.WARNING(
                    f'\nMODO SIMULACIÓN: {count} suscripciones activas se sincronizarían'
                )
            )
            return

        processed, created, est, locked = Subscription.extend_all_active_expenses(
            horizon_months=months_ahead
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'\nListo: {processed} suscripciones, {created} gastos nuevos, '
                f'{est} estimados USD actualizados, {locked} cotizaciones fijadas.'
            )
        )
