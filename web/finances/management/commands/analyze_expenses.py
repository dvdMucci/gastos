from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from collections import defaultdict
import calendar

from finances.models import Expense, Category, PaymentMethod

User = get_user_model()


class Command(BaseCommand):
    help = 'Analiza los gastos de los últimos 6 meses y genera recomendaciones financieras'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username del usuario para analizar (si no se especifica, analiza todos los usuarios)'
        )
        parser.add_argument(
            '--months',
            type=int,
            default=6,
            help='Número de meses hacia atrás para analizar (default: 6)'
        )
        parser.add_argument(
            '--monthly-income',
            type=float,
            default=4300000,
            help='Ingreso mensual promedio del hogar (default: 4300000)'
        )

    def handle(self, *args, **options):
        username = options.get('user')
        months_back = options.get('months')
        monthly_income = Decimal(str(options.get('monthly_income')))

        # Calcular rango de fechas (últimos N meses incluyendo el mes actual)
        today = timezone.now().date()
        start_date = (today.replace(day=1) - relativedelta(months=months_back-1)).replace(day=1)
        end_date = today

        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('ANÁLISIS FINANCIERO - ÚLTIMOS {} MESES'.format(months_back)))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        self.stdout.write(f'Período analizado: {start_date.strftime("%d/%m/%Y")} - {end_date.strftime("%d/%m/%Y")}')
        self.stdout.write(f'Ingreso mensual promedio: ${monthly_income:,.2f}')
        self.stdout.write(f'Ingreso total del período: ${monthly_income * months_back:,.2f}\n')

        if username:
            try:
                users = [User.objects.get(username=username)]
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Usuario {username} no encontrado'))
                return
        else:
            users = User.objects.filter(is_active=True)

        for user in users:
            self.stdout.write(self.style.SUCCESS(f'\n{"="*80}'))
            self.stdout.write(self.style.SUCCESS(f'ANÁLISIS PARA: {user.username}'))
            self.stdout.write(self.style.SUCCESS(f'{"="*80}\n'))

            # Obtener todos los gastos del período
            expenses = Expense.objects.filter(
                user=user,
                date__gte=start_date,
                date__lte=end_date
            ).select_related('category', 'payment_method', 'payment_type')

            if not expenses.exists():
                self.stdout.write(self.style.WARNING('No se encontraron gastos para este período.'))
                continue

            # Análisis general
            total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            total_expenses_credit = expenses.filter(is_credit=True).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            total_expenses_no_credit = expenses.filter(is_credit=False).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            # Gastos pendientes de crédito
            credit_expenses_pending = expenses.filter(
                is_credit=True,
                remaining_amount__gt=0
            ).aggregate(total=Sum('remaining_amount'))['total'] or Decimal('0.00')

            # Análisis por mes
            monthly_expenses = defaultdict(Decimal)
            monthly_counts = defaultdict(int)
            
            for expense in expenses:
                month_key = f"{expense.date.year}-{expense.date.month:02d}"
                monthly_expenses[month_key] += expense.amount
                monthly_counts[month_key] += 1

            # Análisis por categoría
            category_analysis = expenses.values('category__name').annotate(
                total=Sum('amount'),
                count=Count('id'),
                avg=Avg('amount')
            ).order_by('-total')

            # Análisis por método de pago
            payment_method_analysis = expenses.values('payment_method__name').annotate(
                total=Sum('amount'),
                count=Count('id')
            ).order_by('-total')

            # Gastos recurrentes (suscripciones)
            subscription_expenses = expenses.filter(subscription__isnull=False).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')

            # Gastos grandes (mayores al 5% del ingreso mensual)
            large_expense_threshold = monthly_income * Decimal('0.05')
            large_expenses = expenses.filter(amount__gte=large_expense_threshold).order_by('-amount')[:10]

            # Calcular promedios
            avg_monthly_expense = total_expenses / months_back
            avg_monthly_expense_no_credit = total_expenses_no_credit / months_back

            # Mostrar resultados
            self._print_summary(
                total_expenses, total_expenses_no_credit, total_expenses_credit,
                credit_expenses_pending, subscription_expenses,
                monthly_income, months_back, avg_monthly_expense, avg_monthly_expense_no_credit
            )

            self._print_monthly_breakdown(monthly_expenses, monthly_counts, monthly_income)

            self._print_category_analysis(category_analysis, total_expenses)

            self._print_payment_method_analysis(payment_method_analysis, total_expenses)

            if large_expenses.exists():
                self._print_large_expenses(large_expenses, large_expense_threshold)

            # Generar recomendaciones
            self._generate_recommendations(
                total_expenses, monthly_income, months_back,
                category_analysis, payment_method_analysis,
                subscription_expenses, credit_expenses_pending,
                avg_monthly_expense, avg_monthly_expense_no_credit
            )

    def _print_summary(self, total_expenses, total_no_credit, total_credit, 
                      credit_pending, subscriptions, monthly_income, months, 
                      avg_monthly, avg_monthly_no_credit):
        """Imprime el resumen general"""
        total_income = monthly_income * months
        
        self.stdout.write(self.style.SUCCESS('\n📊 RESUMEN GENERAL'))
        self.stdout.write('-' * 80)
        self.stdout.write(f'Total de gastos (6 meses):        ${total_expenses:,.2f}')
        self.stdout.write(f'  - Gastos sin crédito:           ${total_no_credit:,.2f}')
        self.stdout.write(f'  - Gastos a crédito:             ${total_credit:,.2f}')
        self.stdout.write(f'  - Créditos pendientes:          ${credit_pending:,.2f}')
        self.stdout.write(f'  - Suscripciones:                ${subscriptions:,.2f}')
        self.stdout.write('')
        self.stdout.write(f'Promedio mensual total:           ${avg_monthly:,.2f}')
        self.stdout.write(f'Promedio mensual (sin crédito):   ${avg_monthly_no_credit:,.2f}')
        self.stdout.write('')
        self.stdout.write(f'Ingreso total del período:        ${total_income:,.2f}')
        self.stdout.write(f'Balance (Ingreso - Gastos):       ${total_income - total_expenses:,.2f}')
        
        # Porcentaje de gasto sobre ingreso
        expense_percentage = (total_expenses / total_income * 100) if total_income > 0 else 0
        monthly_percentage = (avg_monthly / monthly_income * 100) if monthly_income > 0 else 0
        
        self.stdout.write('')
        self.stdout.write(f'Gasto sobre ingreso (período):    {expense_percentage:.2f}%')
        self.stdout.write(f'Gasto sobre ingreso (mensual):    {monthly_percentage:.2f}%')
        
        if expense_percentage > 100:
            self.stdout.write(self.style.ERROR('⚠️  GASTAS MÁS DE LO QUE GANAS'))
        elif expense_percentage > 90:
            self.stdout.write(self.style.WARNING('⚠️  Estás gastando más del 90% de tus ingresos'))
        elif expense_percentage > 80:
            self.stdout.write(self.style.WARNING('⚠️  Estás gastando más del 80% de tus ingresos'))
        elif expense_percentage < 50:
            self.stdout.write(self.style.SUCCESS('✅ Excelente control de gastos'))
        elif expense_percentage < 70:
            self.stdout.write(self.style.SUCCESS('✅ Buen control de gastos'))

    def _print_monthly_breakdown(self, monthly_expenses, monthly_counts, monthly_income):
        """Imprime el desglose mensual"""
        self.stdout.write(self.style.SUCCESS('\n📅 DESGLOSE MENSUAL'))
        self.stdout.write('-' * 80)
        self.stdout.write(f'{"Mes":<15} {"Total":<20} {"Cantidad":<15} {"% Ingreso":<15} {"Estado":<15}')
        self.stdout.write('-' * 80)
        
        for month_key in sorted(monthly_expenses.keys()):
            year, month = month_key.split('-')
            month_name = calendar.month_name[int(month)]
            total = monthly_expenses[month_key]
            count = monthly_counts[month_key]
            percentage = (total / monthly_income * 100) if monthly_income > 0 else 0
            
            if percentage > 100:
                status = self.style.ERROR('⚠️ Crítico')
            elif percentage > 90:
                status = self.style.WARNING('⚠️ Alto')
            elif percentage > 80:
                status = self.style.WARNING('⚠️ Moderado')
            else:
                status = self.style.SUCCESS('✅ Normal')
            
            self.stdout.write(
                f'{month_name[:3]} {year:<10} ${total:>15,.2f} {count:>10} gastos  '
                f'{percentage:>6.1f}%      {status}'
            )

    def _print_category_analysis(self, category_analysis, total_expenses):
        """Imprime el análisis por categoría"""
        self.stdout.write(self.style.SUCCESS('\n🏷️  ANÁLISIS POR CATEGORÍA'))
        self.stdout.write('-' * 80)
        self.stdout.write(f'{"Categoría":<25} {"Total":<20} {"Cantidad":<15} {"Promedio":<15} {"% Total":<10}')
        self.stdout.write('-' * 80)
        
        for item in category_analysis[:10]:  # Top 10 categorías
            category_name = item['category__name']
            total = item['total']
            count = item['count']
            avg = item['avg']
            percentage = (total / total_expenses * 100) if total_expenses > 0 else 0
            
            self.stdout.write(
                f'{category_name:<25} ${total:>15,.2f} {count:>10} gastos  '
                f'${avg:>10,.2f}  {percentage:>6.1f}%'
            )

    def _print_payment_method_analysis(self, payment_method_analysis, total_expenses):
        """Imprime el análisis por método de pago"""
        self.stdout.write(self.style.SUCCESS('\n💳 ANÁLISIS POR MÉTODO DE PAGO'))
        self.stdout.write('-' * 80)
        self.stdout.write(f'{"Método":<25} {"Total":<20} {"Cantidad":<15} {"% Total":<10}')
        self.stdout.write('-' * 80)
        
        for item in payment_method_analysis:
            method_name = item['payment_method__name']
            total = item['total']
            count = item['count']
            percentage = (total / total_expenses * 100) if total_expenses > 0 else 0
            
            # Obtener nombre legible
            method_display = PaymentMethod.objects.get(name=method_name).get_name_display()
            
            self.stdout.write(
                f'{method_display:<25} ${total:>15,.2f} {count:>10} gastos  '
                f'{percentage:>6.1f}%'
            )

    def _print_large_expenses(self, large_expenses, threshold):
        """Imprime los gastos grandes"""
        self.stdout.write(self.style.SUCCESS(f'\n💰 GASTOS GRANDES (≥ ${threshold:,.2f})'))
        self.stdout.write('-' * 80)
        self.stdout.write(f'{"Fecha":<12} {"Categoría":<20} {"Nombre":<30} {"Monto":<15}')
        self.stdout.write('-' * 80)
        
        for expense in large_expenses:
            self.stdout.write(
                f'{expense.date.strftime("%d/%m/%Y"):<12} '
                f'{expense.category.name:<20} '
                f'{expense.name[:28]:<30} '
                f'${expense.amount:>12,.2f}'
            )

    def _generate_recommendations(self, total_expenses, monthly_income, months,
                                 category_analysis, payment_method_analysis,
                                 subscriptions, credit_pending, avg_monthly, avg_monthly_no_credit):
        """Genera recomendaciones financieras"""
        total_income = monthly_income * months
        expense_percentage = (total_expenses / total_income * 100) if total_income > 0 else 0
        monthly_percentage = (avg_monthly / monthly_income * 100) if monthly_income > 0 else 0
        
        self.stdout.write(self.style.SUCCESS('\n💡 RECOMENDACIONES FINANCIERAS'))
        self.stdout.write('=' * 80)
        
        recommendations = []
        
        # Recomendación 1: Control general de gastos
        if expense_percentage > 100:
            recommendations.append({
                'priority': 'CRÍTICA',
                'title': 'Gastas más de lo que ganas',
                'description': f'Estás gastando ${total_expenses - total_income:,.2f} más de lo que ingresas. '
                              f'Necesitas reducir gastos inmediatamente o aumentar ingresos.',
                'action': 'Revisa todos tus gastos y elimina los no esenciales. Considera buscar ingresos adicionales.'
            })
        elif expense_percentage > 90:
            recommendations.append({
                'priority': 'ALTA',
                'title': 'Gastas más del 90% de tus ingresos',
                'description': f'Estás gastando {expense_percentage:.1f}% de tus ingresos. '
                              f'No tienes margen para ahorros o imprevistos.',
                'action': 'Reduce gastos en al menos un 10-15% para crear un colchón de seguridad.'
            })
        elif expense_percentage > 80:
            recommendations.append({
                'priority': 'MEDIA',
                'title': 'Gastas más del 80% de tus ingresos',
                'description': f'Estás gastando {expense_percentage:.1f}% de tus ingresos. '
                              f'Es recomendable mantener los gastos por debajo del 80%.',
                'action': 'Identifica categorías donde puedas reducir gastos para llegar al 70-75%.'
            })
        else:
            savings = total_income - total_expenses
            savings_percentage = (savings / total_income * 100) if total_income > 0 else 0
            recommendations.append({
                'priority': 'INFO',
                'title': 'Buen control de gastos',
                'description': f'Estás ahorrando ${savings:,.2f} ({savings_percentage:.1f}% de tus ingresos).',
                'action': 'Mantén este nivel de gastos y considera invertir tus ahorros.'
            })

        # Recomendación 2: Gastos a crédito
        if credit_pending > monthly_income * Decimal('0.3'):
            recommendations.append({
                'priority': 'ALTA',
                'title': 'Muchos créditos pendientes',
                'description': f'Tienes ${credit_pending:,.2f} en créditos pendientes, '
                              f'equivalente a más del 30% de tu ingreso mensual.',
                'action': 'Evita nuevos gastos a crédito. Prioriza pagar los créditos existentes.'
            })
        elif credit_pending > 0:
            recommendations.append({
                'priority': 'MEDIA',
                'title': 'Créditos pendientes',
                'description': f'Tienes ${credit_pending:,.2f} en créditos pendientes.',
                'action': 'Considera pagar los créditos antes de hacer nuevas compras.'
            })

        # Recomendación 3: Suscripciones
        monthly_subscriptions = subscriptions / months if months > 0 else Decimal('0')
        if monthly_subscriptions > monthly_income * Decimal('0.1'):
            recommendations.append({
                'priority': 'MEDIA',
                'title': 'Muchas suscripciones',
                'description': f'Gastas ${monthly_subscriptions:,.2f} mensuales en suscripciones '
                              f'({(monthly_subscriptions/monthly_income*100):.1f}% de tu ingreso).',
                'action': 'Revisa tus suscripciones y cancela las que no uses regularmente.'
            })

        # Recomendación 4: Categorías con mayor gasto
        if category_analysis:
            top_category = category_analysis[0]
            top_category_total = top_category['total']
            top_category_percentage = (top_category_total / total_expenses * 100) if total_expenses > 0 else 0
            
            if top_category_percentage > 30:
                recommendations.append({
                    'priority': 'MEDIA',
                    'title': f'Mucho gasto en {top_category["category__name"]}',
                    'description': f'El {top_category_percentage:.1f}% de tus gastos es en {top_category["category__name"]}.',
                    'action': f'Busca formas de reducir gastos en {top_category["category__name"]}: '
                             f'compara precios, busca ofertas, o reduce la frecuencia.'
                })

        # Recomendación 5: Método de pago
        credit_payment = next((item for item in payment_method_analysis if item['payment_method__name'] == 'credito'), None)
        if credit_payment:
            credit_percentage = (credit_payment['total'] / total_expenses * 100) if total_expenses > 0 else 0
            if credit_percentage > 40:
                recommendations.append({
                    'priority': 'ALTA',
                    'title': 'Uso excesivo de tarjeta de crédito',
                    'description': f'El {credit_percentage:.1f}% de tus gastos son con tarjeta de crédito.',
                    'action': 'Intenta usar más efectivo o débito para tener mejor control de tus gastos.'
                })

        # Recomendación 6: Meta de ahorro
        if expense_percentage < 80:
            target_savings = monthly_income * Decimal('0.2')  # 20% de ahorro
            current_savings = monthly_income - avg_monthly
            if current_savings < target_savings:
                recommendations.append({
                    'priority': 'BAJA',
                    'title': 'Aumenta tu ahorro',
                    'description': f'Actualmente ahorras ${current_savings:,.2f} mensuales. '
                                  f'Meta recomendada: ${target_savings:,.2f} (20% del ingreso).',
                    'action': f'Reduce gastos en ${target_savings - current_savings:,.2f} mensuales '
                             f'para alcanzar la meta de ahorro del 20%.'
                })

        # Imprimir recomendaciones
        for i, rec in enumerate(recommendations, 1):
            priority_colors = {
                'CRÍTICA': self.style.ERROR,
                'ALTA': self.style.WARNING,
                'MEDIA': self.style.WARNING,
                'BAJA': self.style.SUCCESS,
                'INFO': self.style.SUCCESS
            }
            color = priority_colors.get(rec['priority'], self.stdout.write)
            
            self.stdout.write('')
            self.stdout.write(color(f'{i}. [{rec["priority"]}] {rec["title"]}'))
            self.stdout.write(f'   {rec["description"]}')
            self.stdout.write(color(f'   💡 Acción: {rec["action"]}'))

        # Resumen final
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('RESUMEN DE ACCIONES PRIORITARIAS'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        critical = [r for r in recommendations if r['priority'] == 'CRÍTICA']
        high = [r for r in recommendations if r['priority'] == 'ALTA']
        
        if critical:
            self.stdout.write(self.style.ERROR('\n⚠️  ACCIONES CRÍTICAS (hacer inmediatamente):'))
            for rec in critical:
                self.stdout.write(f'   • {rec["action"]}')
        
        if high:
            self.stdout.write(self.style.WARNING('\n⚠️  ACCIONES IMPORTANTES (hacer pronto):'))
            for rec in high:
                self.stdout.write(f'   • {rec["action"]}')
        
        # Meta mensual sugerida
        if expense_percentage > 80:
            target_monthly = monthly_income * Decimal('0.75')  # 75% del ingreso
            reduction_needed = avg_monthly - target_monthly
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🎯 META MENSUAL SUGERIDA:'))
            self.stdout.write(f'   Gasto mensual objetivo: ${target_monthly:,.2f} (75% del ingreso)')
            self.stdout.write(f'   Reducción necesaria: ${reduction_needed:,.2f} mensuales')
            self.stdout.write(f'   Esto te permitiría ahorrar: ${monthly_income - target_monthly:,.2f} mensuales')
        
        self.stdout.write('')

