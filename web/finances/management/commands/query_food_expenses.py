from django.core.management.base import BaseCommand
from finances.models import Expense, Category, PaymentMethod
from django.utils import timezone
from datetime import datetime
from decimal import Decimal

class Command(BaseCommand):
    help = 'Consulta los gastos de alimentos del mes actual excluyendo créditos'

    def handle(self, *args, **options):
        # Obtener el mes actual
        now = timezone.now()
        year = now.year
        month = now.month
        
        # Categorías relacionadas con alimentos
        food_categories = ['Carnicería', 'Verdulería', 'Supermercado', 'Panadería']
        
        # Obtener las categorías de alimentos
        categories = Category.objects.filter(name__in=food_categories)
        category_ids = list(categories.values_list('id', flat=True))
        
        # Obtener el método de pago de crédito
        credit_payment_method = PaymentMethod.objects.filter(name='credito').first()
        
        if not credit_payment_method:
            self.stdout.write(self.style.ERROR('No se encontró el método de pago CREDITO'))
            return
        
        # Consultar gastos del mes actual
        # Excluir: is_credit=True O payment_method=credito
        expenses = Expense.objects.filter(
            date__year=year,
            date__month=month,
            category_id__in=category_ids
        ).exclude(
            is_credit=True
        ).exclude(
            payment_method=credit_payment_method
        ).select_related('category', 'payment_method', 'payment_type')
        
        # Calcular el total
        total = Decimal('0.00')
        
        self.stdout.write(self.style.SUCCESS(f'\n=== Gastos de Alimentos - {month}/{year} ===\n'))
        self.stdout.write(f'Categorías incluidas: {", ".join(food_categories)}\n')
        self.stdout.write(f'Excluyendo: Gastos con is_credit=True o payment_method=CREDITO\n')
        self.stdout.write('-' * 80)
        
        if not expenses.exists():
            self.stdout.write(self.style.WARNING('No se encontraron gastos de alimentos para este mes.'))
        else:
            for expense in expenses:
                total += expense.amount
                self.stdout.write(
                    f"Fecha: {expense.date.strftime('%d/%m/%Y')} | "
                    f"Categoría: {expense.category.name} | "
                    f"Nombre: {expense.name} | "
                    f"Monto: ${expense.amount} | "
                    f"Método: {expense.payment_method.get_name_display()} | "
                    f"Tipo: {expense.payment_type.get_name_display()}"
                )
            
            self.stdout.write('-' * 80)
            self.stdout.write(self.style.SUCCESS(f'\nTOTAL: ${total}'))
            self.stdout.write(f'\nCantidad de gastos: {expenses.count()}\n')

