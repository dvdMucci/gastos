from django.core.management.base import BaseCommand
from django.utils import timezone
from subscriptions.models import Subscription
from finances.models import Expense
from datetime import datetime, timedelta
import calendar

class Command(BaseCommand):
    help = 'Crea gastos automáticamente para suscripciones que vencen en el próximo mes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--months-ahead',
            type=int,
            default=1,
            help='Número de meses hacia adelante para crear gastos (default: 1)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se haría sin crear los gastos'
        )

    def handle(self, *args, **options):
        months_ahead = options['months_ahead']
        dry_run = options['dry_run']
        
        self.stdout.write(f'Creando gastos para suscripciones en los próximos {months_ahead} meses...')
        
        today = timezone.now().date()
        current_year = today.year
        current_month = today.month
        
        total_created = 0
        total_skipped = 0
        
        for i in range(1, months_ahead + 1):
            month = current_month + i
            year = current_year
            
            while month > 12:
                month -= 12
                year += 1
            
            target_date = datetime(year, month, 1).date()
            
            self.stdout.write(f'\nProcesando mes: {calendar.month_name[month]} {year}')
            
            # Obtener suscripciones activas que vencen en este mes
            subscriptions = Subscription.objects.filter(
                status='active',
                auto_create_expense=True
            )
            
            for subscription in subscriptions:
                # Verificar si ya existe un gasto para esta suscripción en este mes
                existing_expense = Expense.objects.filter(
                    name__icontains=subscription.name,
                    user=subscription.user,
                    date__year=year,
                    date__month=month,
                    amount=subscription.amount
                ).first()
                
                if existing_expense:
                    self.stdout.write(f'  - Saltando {subscription.name}: ya existe gasto para {month}/{year}')
                    total_skipped += 1
                    continue
                
                # Crear el gasto
                if not dry_run:
                    expense = Expense.objects.create(
                        user=subscription.user,
                        date=target_date,
                        name=f"{subscription.name} (Suscripción)",
                        amount=subscription.amount,
                        category=subscription.category,
                        payment_method=subscription.payment_method,
                        payment_type=subscription.payment_type,
                        description=f"Suscripción automática: {subscription.description or 'Sin descripción'}",
                        is_credit=False
                    )
                    
                    self.stdout.write(f'  ✓ Creado gasto: {expense.name} - ${expense.amount}')
                else:
                    self.stdout.write(f'  ✓ Se crearía gasto: {subscription.name} - ${subscription.amount}')
                
                total_created += 1
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n🔍 MODO SIMULACIÓN: Se crearían {total_created} gastos y se saltarían {total_skipped}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Completado! Se crearon {total_created} gastos y se saltaron {total_skipped}'
                )
            )
