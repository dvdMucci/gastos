from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from forecasts.models import ExpenseForecast

User = get_user_model()

class Command(BaseCommand):
    help = 'Generar sugerencias automáticas de gastos basadas en datos históricos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username del usuario para generar sugerencias'
        )
        parser.add_argument(
            '--months',
            type=int,
            default=6,
            help='Número de meses hacia atrás para analizar (default: 6)'
        )

    def handle(self, *args, **options):
        username = options.get('user')
        months_back = options.get('months')
        
        if username:
            try:
                user = User.objects.get(username=username)
                self.stdout.write(f'Generando sugerencias para usuario: {user.username}')
                suggestions = ExpenseForecast.generate_automatic_suggestions(user, months_back)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Se generaron {len(suggestions)} sugerencias automáticas para {user.username}'
                    )
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Usuario {username} no encontrado')
                )
        else:
            # Generar para todos los usuarios
            users = User.objects.filter(is_active=True)
            total_suggestions = 0
            
            for user in users:
                self.stdout.write(f'Generando sugerencias para usuario: {user.username}')
                suggestions = ExpenseForecast.generate_automatic_suggestions(user, months_back)
                total_suggestions += len(suggestions)
                self.stdout.write(f'  - {len(suggestions)} sugerencias generadas')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Se generaron {total_suggestions} sugerencias automáticas en total'
                )
            )
