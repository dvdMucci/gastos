from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from forecasts.models import MonthlyForecast

User = get_user_model()

class Command(BaseCommand):
    help = 'Generar estimaciones mensuales para usuarios'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username del usuario para generar estimaciones'
        )
        parser.add_argument(
            '--months-back',
            type=int,
            default=6,
            help='Número de meses hacia atrás (default: 6)'
        )
        parser.add_argument(
            '--months-forward',
            type=int,
            default=12,
            help='Número de meses hacia adelante (default: 12)'
        )

    def handle(self, *args, **options):
        username = options.get('user')
        months_back = options.get('months_back')
        months_forward = options.get('months_forward')

        if username:
            try:
                user = User.objects.get(username=username)
                self.stdout.write(f'Generando estimaciones para usuario: {user.username}')
                MonthlyForecast.generate_forecasts(user, months_back=months_back, months_forward=months_forward)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Estimaciones generadas para {user.username}'
                    )
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Usuario {username} no encontrado')
                )
        else:
            # Generar para todos los usuarios
            users = User.objects.filter(is_active=True)

            for user in users:
                self.stdout.write(f'Generando estimaciones para usuario: {user.username}')
                MonthlyForecast.generate_forecasts(user, months_back=months_back, months_forward=months_forward)

            self.stdout.write(
                self.style.SUCCESS(
                    f'Estimaciones generadas para {users.count()} usuarios'
                )
            )