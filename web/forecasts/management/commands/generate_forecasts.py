from django.core.management.base import BaseCommand
from forecasts.models import MonthlyForecast, ExpenseForecast
from django.utils import timezone
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Generar estimaciones mensuales para el sistema de forecasts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--months-back',
            type=int,
            default=6,
            help='Número de meses hacia atrás para generar estimaciones'
        )
        parser.add_argument(
            '--months-forward',
            type=int,
            default=12,
            help='Número de meses hacia adelante para generar estimaciones'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la regeneración de estimaciones existentes'
        )

    def handle(self, *args, **options):
        months_back = options['months_back']
        months_forward = options['months_forward']
        force = options['force']

        self.stdout.write(
            self.style.SUCCESS(
                f'Generando estimaciones para {months_back} meses atrás y {months_forward} meses adelante...'
            )
        )

        if force:
            # Eliminar estimaciones existentes
            MonthlyForecast.objects.all().delete()
            self.stdout.write(
                self.style.WARNING('Estimaciones existentes eliminadas')
            )

        # Generar estimaciones
        MonthlyForecast.generate_forecasts(
            months_back=months_back,
            months_forward=months_forward
        )

        # Verificar resultados
        total_forecasts = MonthlyForecast.objects.count()
        active_forecasts = ExpenseForecast.objects.filter(is_active=True).count()

        self.stdout.write(
            self.style.SUCCESS(
                f'Se generaron {total_forecasts} estimaciones mensuales'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Hay {active_forecasts} estimaciones activas'
            )
        )

        # Mostrar resumen de las estimaciones generadas
        forecasts = MonthlyForecast.objects.all().order_by('month')
        for forecast in forecasts:
            self.stdout.write(
                f'  - {forecast.month.strftime("%B %Y")}: '
                f'Total: ${forecast.total_projected:.2f}'
            )
