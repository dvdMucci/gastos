from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from datetime import datetime, timedelta
import calendar
from dateutil.relativedelta import relativedelta
from finances.models import Category, PaymentMethod, PaymentType
from accounts.models import CustomUser

class ExpenseForecast(models.Model):
    """Modelo para estimaciones futuras de gastos"""
    
    EXPENSE_TYPE_CHOICES = [
        ('food', 'Comida'),
        ('health', 'Salud'),
        ('transport', 'Transporte'),
        ('entertainment', 'Entretenimiento'),
        ('utilities', 'Servicios'),
        ('shopping', 'Compras'),
        ('other', 'Otros'),
    ]
    
    confidence_level = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        verbose_name='Nivel de Confianza', 
        default=0.50
    )

    FREQUENCY_CHOICES = [
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('biannual', 'Semestral'),
        ('annual', 'Anual'),
        ('variable', 'Variable'),
        ('one_time', 'Único'),
    ]
    
    CONFIDENCE_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
    ]
    
    # Campos básicos
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Usuario")
    name = models.CharField(max_length=200, verbose_name="Nombre del gasto")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto estimado")
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPE_CHOICES, default='other', verbose_name='Tipo de Gasto')
    
    # Categoría y método de pago
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Categoría")
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, verbose_name="Método de pago")
    payment_type = models.ForeignKey(PaymentType, on_delete=models.PROTECT, verbose_name="Tipo de pago")
    
    # Fechas y frecuencia
    forecast_type = models.CharField(max_length=20, choices=[
        ('subscription', 'Suscripción'),
        ('credit', 'Crédito'),
        ('estimated', 'Estimado'),
        ('recurring', 'Recurrente'),
    ], default='estimated', verbose_name="Tipo de estimación")
    start_date = models.DateField(verbose_name="Fecha de inicio")
    end_date = models.DateField(verbose_name="Fecha de finalización")
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly', verbose_name="Frecuencia")
    confidence = models.CharField(max_length=20, choices=CONFIDENCE_CHOICES, default='medium', verbose_name='Confianza')
    
    # Campos para seguimiento
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    is_automatic_suggestion = models.BooleanField(default=False, verbose_name="Sugerencia Automática")
    suggested_based_on_months = models.IntegerField(default=6, verbose_name="Basado en Últimos Meses")
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    
    class Meta:
        verbose_name = "Estimación de Gasto"
        verbose_name_plural = "Estimaciones de Gastos"
        ordering = ['start_date', 'name']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['user', 'is_automatic_suggestion']),
            models.Index(fields=['user', 'start_date']),
            models.Index(fields=['user', 'end_date']),
            models.Index(fields=['category']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['payment_type']),
        ]
    
    def __str__(self):
        return f"{self.name} - ${self.amount} ({self.get_frequency_display()})"
    
    def get_total_forecasted(self):
        """Calcula el total estimado para el período"""
        if self.frequency == 'one_time':
            return self.amount
        
        # Calcular cuántos períodos hay entre start_date y end_date
        start = self.start_date
        end = self.end_date
        
        if self.frequency == 'monthly':
            months = (end.year - start.year) * 12 + (end.month - start.month) + 1
            return self.amount * months
        elif self.frequency == 'quarterly':
            months = (end.year - start.year) * 12 + (end.month - start.month) + 1
            quarters = (months + 2) // 3  # Redondear hacia arriba
            return self.amount * quarters
        elif self.frequency == 'biannual':
            months = (end.year - start.year) * 12 + (end.month - start.month) + 1
            semesters = (months + 5) // 6  # Redondear hacia arriba
            return self.amount * semesters
        elif self.frequency == 'annual':
            years = (end.year - start.year) + 1
            return self.amount * years
        
        return self.amount
    
    def get_monthly_average(self):
        """Calcula el promedio mensual del gasto"""
        if self.frequency == 'one_time':
            # Para gastos únicos, distribuir el monto en el período
            months = (self.end_date.year - self.start_date.year) * 12 + (self.end_date.month - self.start_date.month) + 1
            return self.amount / months if months > 0 else 0
        
        # Para gastos recurrentes, convertir a promedio mensual
        if self.frequency == 'monthly':
            return self.amount
        elif self.frequency == 'quarterly':
            return self.amount / 3
        elif self.frequency == 'biannual':
            return self.amount / 6
        elif self.frequency == 'annual':
            return self.amount / 12
        
        return self.amount
    
    def get_forecast_for_month(self, year, month):
        """Obtiene la estimación para un mes específico"""
        if not self.is_active:
            return 0
        
        # Verificar si el mes está en el rango
        month_date = datetime(year, month, 1).date()
        if month_date < self.start_date or month_date > self.end_date:
            return 0
        
        if self.frequency == 'one_time':
            # Para gastos únicos, solo en el mes de inicio
            if month_date == self.start_date:
                return self.amount
            return 0
        
        # Para gastos recurrentes
        if self.frequency == 'monthly':
            return self.amount
        elif self.frequency == 'quarterly':
            # Verificar si es el mes correcto para el trimestre
            quarter_start_month = ((month - 1) // 3) * 3 + 1
            if month == quarter_start_month:
                return self.amount
            return 0
        elif self.frequency == 'biannual':
            # Verificar si es el mes correcto para el semestre
            semester_start_month = ((month - 1) // 6) * 6 + 1
            if month == semester_start_month:
                return self.amount
            return 0
        elif self.frequency == 'annual':
            # Verificar si es el mes correcto para el año
            if month == self.start_date.month:
                return self.amount
            return 0
        
        return 0

    @classmethod
    def generate_automatic_suggestions(cls, user, months_back=6):
        """Generar sugerencias automáticas basadas en datos históricos"""
        from finances.models import Expense
        
        # Obtener fecha de inicio para el análisis
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=months_back*30)
        
        # Obtener gastos de los últimos meses (excluyendo créditos y suscripciones)
        expenses = Expense.objects.filter(
            user=user,
            date__range=[start_date, end_date],
            is_credit=False,
            subscription__isnull=True
        )
        
        # Agrupar por categoría y calcular promedios
        category_totals = {}
        category_counts = {}
        
        for expense in expenses:
            category = expense.category
            if category not in category_totals:
                category_totals[category] = 0
                category_counts[category] = 0
            
            category_totals[category] += expense.amount
            category_counts[category] += 1
        
        # Crear sugerencias automáticas
        suggestions = []
        for category, total in category_totals.items():
            count = category_counts[category]
            if count >= 2:  # Solo sugerir si hay al menos 2 gastos
                avg_amount = total / count
                monthly_avg = avg_amount * (12 / months_back)  # Proyectar a 12 meses
                
                # Determinar tipo de gasto basado en la categoría
                expense_type = cls._categorize_expense_type(category.name)
                
                # Determinar confianza basada en la cantidad de datos
                if count >= 5:
                    confidence = 'high'
                elif count >= 3:
                    confidence = 'medium'
                else:
                    confidence = 'low'
                
                # Crear o actualizar la sugerencia
                suggestion, created = cls.objects.get_or_create(
                    name=f"Estimación automática - {category.name}",
                    category=category,
                    expense_type=expense_type,
                    defaults={
                        'amount': monthly_avg,
                        'frequency': 'monthly',
                        'confidence': confidence,
                        'is_active': False,  # Las sugerencias automáticas no están activas por defecto
                        'is_automatic_suggestion': True,
                        'suggested_based_on_months': months_back,
                    }
                )
                
                if not created:
                    # Actualizar monto y confianza si ya existe
                    suggestion.amount = monthly_avg
                    suggestion.confidence = confidence
                    suggestion.suggested_based_on_months = months_back
                    suggestion.save()
                
                suggestions.append(suggestion)
        
        return suggestions
    
    @classmethod
    def _categorize_expense_type(cls, category_name):
        """Categorizar el tipo de gasto basado en el nombre de la categoría"""
        category_lower = category_name.lower()
        
        if any(word in category_lower for word in ['comida', 'alimento', 'restaurante', 'supermercado']):
            return 'food'
        elif any(word in category_lower for word in ['salud', 'medico', 'farmacia', 'hospital']):
            return 'health'
        elif any(word in category_lower for word in ['transporte', 'combustible', 'taxi', 'uber']):
            return 'transport'
        elif any(word in category_lower for word in ['entretenimiento', 'cine', 'teatro', 'deporte']):
            return 'entertainment'
        elif any(word in category_lower for word in ['servicio', 'luz', 'agua', 'gas', 'internet']):
            return 'utilities'
        elif any(word in category_lower for word in ['ropa', 'zapatos', 'accesorio', 'tecnologia']):
            return 'shopping'
        else:
            return 'other'
    
    def get_monthly_amount(self):
        """Obtener monto mensual basado en la frecuencia"""
        if self.frequency == 'monthly':
            return self.amount
        elif self.frequency == 'quarterly':
            return self.amount / 3
        elif self.frequency == 'biannual':
            return self.amount / 6
        elif self.frequency == 'annual':
            return self.amount / 12
        else:  # variable
            return self.amount

class MonthlyForecast(models.Model):
    """Resumen mensual de estimaciones futuras"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Usuario")
    month = models.DateField(verbose_name='Mes')
    
    # Datos históricos reales
    actual_subscriptions = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Suscripciones Reales')
    actual_credits = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Créditos Reales')
    actual_other_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Otros Gastos Reales')
    
    # Datos del mes actual (estimación vs real)
    current_month_estimated = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Estimación del Mes Actual')
    current_month_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Gastos Reales del Mes Actual')
    
    # Datos futuros proyectados con componentes real y estimado
    future_real_subscriptions = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Suscripciones Reales Futuras')
    future_real_credits = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Créditos Reales Futuros')
    future_estimated_credits = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Créditos Estimados Futuros')
    future_estimated_other = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Otros Estimados Futuros')

    # Totales futuros bifurcados
    future_real_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Total Real Futuro')
    future_estimated_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Total Estimado Futuro')
    
    # Campos de auditoría
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Fecha de Creación')
    updated_at = models.DateTimeField(default=timezone.now, verbose_name='Última Actualización')
    
    class Meta:
        verbose_name = 'Estimación Mensual'
        verbose_name_plural = 'Estimaciones Mensuales'
        ordering = ['user', 'month']
        unique_together = ['user', 'month']
        indexes = [
            models.Index(fields=['user', 'month']),
            models.Index(fields=['user']),
            models.Index(fields=['month']),
        ]
    
    def __str__(self):
        total = self.future_estimated_total or self.current_month_estimated or (self.actual_subscriptions + self.actual_credits + self.actual_other_expenses)
        return f"{self.month.strftime('%B %Y')} - ${total:.2f}"
    
    @classmethod
    def _ready_cache_key(cls, user, months_back, months_forward):
        # v2: suscripciones futuras e ingresos del gráfico usan agregación del hogar
        return f"forecasts_ready_v2_{user.id}_{months_back}_{months_forward}"

    @classmethod
    def invalidate_forecast_cache(cls, user=None):
        """
        Invalidate cached forecast readiness flags.
        If user is None, invalidates for all active users (household data changed).
        """
        from django.contrib.auth import get_user_model

        users = [user] if user is not None else get_user_model().objects.filter(is_active=True)
        for u in users:
            for months_back in (3, 6, 12):
                for months_forward in (6, 12, 24):
                    try:
                        cache.delete(cls._ready_cache_key(u, months_back, months_forward))
                    except Exception:
                        pass

    @classmethod
    def ensure_forecasts(cls, user, months_back=6, months_forward=12):
        """
        Return existing monthly forecasts when the Redis cache says they are fresh.
        Regenerates only on cache miss, empty data, or after invalidate_forecast_cache().
        """
        cache_key = cls._ready_cache_key(user, months_back, months_forward)
        try:
            if cache.get(cache_key) and cls.objects.filter(user=user).exists():
                return cls.objects.filter(user=user).count()
        except Exception:
            pass
        return cls.generate_forecasts(user, months_back=months_back, months_forward=months_forward)

    @classmethod
    def generate_forecasts(cls, user, months_back=6, months_forward=12):
        """Regenerate monthly forecasts and mark the Redis cache as fresh."""
        # Delete all existing MonthlyForecast records para regenerar con datos actuales
        cls.objects.filter(user=user).delete()

        cache_key = cls._ready_cache_key(user, months_back, months_forward)

        today = timezone.now().date()
        current_month = today.replace(day=1)

        # Generar estimaciones para meses pasados, actual y futuros
        for i in range(-months_back, months_forward + 1):
            if i < 0:
                month_date = (current_month + relativedelta(months=i)).replace(day=1)
                cls._generate_historical_month(user, month_date)
            elif i == 0:
                cls._generate_current_month(user, current_month)
            else:
                month_date = (current_month + relativedelta(months=i)).replace(day=1)
                cls._generate_future_month(user, month_date)

        try:
            # Fresh until invalidated by data changes (or max 24h safety TTL)
            cache.set(cache_key, True, 60 * 60 * 24)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Cache set failed for key {cache_key}: {e}")

        return cls.objects.filter(user=user).count()
    
    @classmethod
    def _generate_historical_month(cls, user, month_date):
        """Generar datos para un mes histórico"""
        from finances.models import Expense
        from subscriptions.models import Subscription

        # Obtener gastos reales del mes
        start_date = month_date
        if month_date.month == 12:
            end_date = month_date.replace(year=month_date.year + 1, month=1) - timedelta(days=1)
        else:
            end_date = month_date.replace(month=month_date.month + 1) - timedelta(days=1)

        expenses = Expense.objects.filter(date__range=[start_date, end_date])

        # Calcular totales por tipo
        subscriptions_total = expenses.filter(subscription__isnull=False).aggregate(
            total=models.Sum('amount'))['total'] or 0
        credits_total = expenses.filter(is_credit=True).aggregate(
            total=models.Sum('amount'))['total'] or 0
        other_total = expenses.filter(
            is_credit=False,
            subscription__isnull=True
        ).aggregate(total=models.Sum('amount'))['total'] or 0

        # Crear o actualizar el registro
        forecast, created = cls.objects.get_or_create(
            user=user,
            month=month_date,
            defaults={
                'actual_subscriptions': subscriptions_total,
                'actual_credits': credits_total,
                'actual_other_expenses': other_total
            }
        )

        if not created:
            forecast.actual_subscriptions = subscriptions_total
            forecast.actual_credits = credits_total
            forecast.actual_other_expenses = other_total
            forecast.save()
    
    @classmethod
    def _generate_current_month(cls, user, month_date):
        """Generar datos para el mes actual - cálculo en tiempo real"""
        from finances.models import Expense
        from subscriptions.models import Subscription
        from .models import ExpenseForecast

        today = timezone.now().date()
        start_date = month_date
        if month_date.month == 12:
            end_date = month_date.replace(year=month_date.year + 1, month=1) - timedelta(days=1)
        else:
            end_date = month_date.replace(month=month_date.month + 1) - timedelta(days=1)

        # 1. GASTOS REALES hasta HOY (tiempo real) - todos los usuarios
        # Solo incluir gastos hasta la fecha actual
        actual_expenses = Expense.objects.filter(
            date__range=[start_date, today]
        )
        actual_total = actual_expenses.aggregate(
            total=models.Sum('amount'))['total'] or 0

        # 2. ESTIMADO para el mes completo basado en promedio de últimos 6 meses
        # Promedio de gastos REALES TOTALES de los últimos 6 meses completos
        avg_total_last_6_months = cls._calculate_average_total_last_6_months(user, month_date)
        
        # El estimado total del mes es el promedio de los últimos 6 meses
        estimated_total = avg_total_last_6_months

        # Crear o actualizar el registro
        forecast, created = cls.objects.get_or_create(
            user=user,
            month=month_date,
            defaults={
                'current_month_estimated': estimated_total,
                'current_month_actual': actual_total
            }
        )

        if not created:
            forecast.current_month_estimated = estimated_total
            forecast.current_month_actual = actual_total
            forecast.save()
    
    @classmethod
    def _calculate_average_credit_last_6_months(cls, user, target_month):
        """Calcular el promedio de gastos en créditos de los últimos 6 meses"""
        from finances.models import Expense

        # Obtener los últimos 6 meses antes del mes objetivo
        end_date = target_month - timedelta(days=1)  # Último día del mes anterior
        start_date = end_date - relativedelta(months=6) + timedelta(days=1)  # Primer día 6 meses atrás

        # Gastos en créditos en ese período
        credit_expenses = Expense.objects.filter(
            user=user,
            is_credit=True,
            date__range=[start_date, end_date]
        )

        total_credit = credit_expenses.aggregate(
            total=models.Sum('amount'))['total'] or 0

        # Promedio mensual
        return total_credit / 6

    @classmethod
    def _get_recurrent_categories_config(cls):
        """Configuración de categorías recurrentes y sus características"""
        # Si hay detección automática, se combina con la configuración manual
        auto_detected = cls._auto_detect_recurrent_categories()
        manual_config = {
            'monthly_fixed': ['Luz', 'Gas', 'Internet', 'Agua'],  # Servicios fijos mensuales
            'variable_recurrent': ['Supermercado', 'Combustible'],  # Recurrentes pero variables
        }
        
        # Combinar configuración manual con detección automática
        for cat_name, cat_info in auto_detected.items():
            if cat_info['frequency'] >= 0.8:  # Muy recurrente (80%+ de meses con gastos)
                if cat_name not in manual_config['monthly_fixed']:
                    manual_config['monthly_fixed'].append(cat_name)
            elif cat_info['frequency'] >= 0.5:  # Moderadamente recurrente
                if cat_name not in manual_config['variable_recurrent']:
                    manual_config['variable_recurrent'].append(cat_name)
        
        return manual_config
    
    @classmethod
    def _auto_detect_recurrent_categories(cls, min_months_with_expenses=4):
        """
        Detectar automáticamente categorías recurrentes basándose en frecuencia de gastos
        Retorna dict con información de cada categoría detectada
        """
        from finances.models import Expense, Category
        from django.db.models import Count, Sum
        from collections import defaultdict
        
        start_date, end_date = cls._get_last_6_complete_months_range()
        
        # Obtener todos los gastos de los últimos 6 meses
        expenses = Expense.objects.filter(date__range=[start_date, end_date])
        
        # Agrupar por categoría y mes
        category_month_data = defaultdict(lambda: defaultdict(float))
        categories = set()
        
        current_date = start_date
        months_list = []
        
        while current_date <= end_date:
            if current_date.month == 12:
                month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
            
            month_key = f"{current_date.year}-{current_date.month:02d}"
            months_list.append(month_key)
            
            month_expenses = expenses.filter(date__range=[current_date, month_end])
            for expense in month_expenses:
                cat_name = expense.category.name
                categories.add(cat_name)
                category_month_data[cat_name][month_key] += float(expense.amount)
            
            current_date = (current_date + relativedelta(months=1)).replace(day=1)
        
        # Analizar cada categoría
        detected_categories = {}
        total_months = len(months_list)
        
        for cat_name in categories:
            months_with_expenses = len([m for m in months_list if category_month_data[cat_name][m] > 0])
            frequency = months_with_expenses / total_months if total_months > 0 else 0
            
            if months_with_expenses >= min_months_with_expenses:
                total_amount = sum(category_month_data[cat_name].values())
                monthly_avg = total_amount / months_with_expenses if months_with_expenses > 0 else 0
                
                detected_categories[cat_name] = {
                    'frequency': frequency,
                    'months_with_expenses': months_with_expenses,
                    'total_months': total_months,
                    'total_amount': total_amount,
                    'monthly_average': monthly_avg,
                }
        
        return detected_categories
    
    @classmethod
    def _calculate_time_weights(cls):
        """Pesos para promedio ponderado (más peso a meses recientes)"""
        return [0.10, 0.10, 0.15, 0.15, 0.25, 0.25]  # Mes 6 a Mes 1 (más antiguo a más reciente)
    
    @classmethod
    def _get_last_6_complete_months_range(cls):
        """Obtener rango de fechas de los últimos 6 meses completos"""
        today = timezone.now().date()
        # Último día del mes anterior a hoy (mes completo más reciente)
        if today.month == 1:
            last_month_end = today.replace(year=today.year - 1, month=12, day=31)
        else:
            last_month_end = today.replace(month=today.month - 1, day=calendar.monthrange(today.year, today.month - 1)[1])
        
        # Primer día del mes 6 meses atrás
        start_date = (last_month_end - relativedelta(months=5)).replace(day=1)
        end_date = last_month_end
        
        return start_date, end_date
    
    @classmethod
    def _calculate_category_monthly_averages(cls, start_date, end_date):
        """Calcular promedio mensual por categoría para los últimos 6 meses con análisis completo"""
        from finances.models import Expense, Category
        from django.db.models import Sum
        import statistics
        
        categories_config = cls._get_recurrent_categories_config()
        all_recurrent_cats = categories_config['monthly_fixed'] + categories_config['variable_recurrent']
        
        category_averages = {}
        
        # Calcular promedio por categoría recurrente con análisis completo
        for cat_name in all_recurrent_cats:
            try:
                category = Category.objects.get(name=cat_name)
                
                # Obtener gastos mensuales para análisis
                monthly_amounts = []
                current_date = start_date
                
                while current_date <= end_date:
                    if current_date.month == 12:
                        month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
                    else:
                        month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
                    
                    month_expenses = Expense.objects.filter(
                        category=category,
                        date__range=[current_date, month_end]
                    )
                    month_total = month_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
                    monthly_amounts.append(float(month_total))
                    
                    current_date = (current_date + relativedelta(months=1)).replace(day=1)
                
                # Calcular estadísticas
                total = sum(monthly_amounts)
                monthly_avg = total / 6 if len(monthly_amounts) > 0 else 0
                
                # Análisis de tendencia
                trend = cls._calculate_trend(monthly_amounts)
                
                # Indicador de confianza (basado en variabilidad)
                confidence = cls._calculate_confidence(monthly_amounts, monthly_avg)
                
                # Gastos totales
                expenses = Expense.objects.filter(
                    category=category,
                    date__range=[start_date, end_date]
                )
                
                category_averages[cat_name] = {
                    'monthly_average': monthly_avg,
                    'total_amount': total,
                    'expense_count': expenses.count(),
                    'category_type': 'monthly_fixed' if cat_name in categories_config['monthly_fixed'] else 'variable_recurrent',
                    'trend': trend,  # 'increasing', 'decreasing', 'stable'
                    'trend_percentage': trend.get('percentage', 0),
                    'confidence': confidence,  # 0-1
                    'confidence_level': cls._get_confidence_level(confidence),
                    'monthly_amounts': monthly_amounts,
                    'variability': statistics.stdev(monthly_amounts) if len(monthly_amounts) > 1 else 0,
                }
            except Category.DoesNotExist:
                continue
        
        return category_averages
    
    @classmethod
    def _calculate_trend(cls, monthly_amounts):
        """
        Calcular tendencia de una serie de valores mensuales
        Retorna: {'direction': 'increasing'|'decreasing'|'stable', 'percentage': float}
        """
        if len(monthly_amounts) < 2:
            return {'direction': 'stable', 'percentage': 0}
        
        # Calcular promedio de primeros 3 meses vs últimos 3 meses
        first_half = monthly_amounts[:3] if len(monthly_amounts) >= 3 else monthly_amounts[:len(monthly_amounts)//2]
        second_half = monthly_amounts[-3:] if len(monthly_amounts) >= 3 else monthly_amounts[len(monthly_amounts)//2:]
        
        avg_first = sum(first_half) / len(first_half) if first_half else 0
        avg_second = sum(second_half) / len(second_half) if second_half else 0
        
        if avg_first == 0:
            return {'direction': 'stable', 'percentage': 0}
        
        change_percentage = ((avg_second - avg_first) / avg_first) * 100
        
        # Umbral del 5% para considerar cambio significativo
        if abs(change_percentage) < 5:
            direction = 'stable'
        elif change_percentage > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'
        
        return {
            'direction': direction,
            'percentage': abs(change_percentage)
        }
    
    @classmethod
    def _calculate_confidence(cls, monthly_amounts, average):
        """
        Calcular nivel de confianza basado en variabilidad
        Retorna valor entre 0 y 1 (1 = muy confiable, 0 = poco confiable)
        """
        if len(monthly_amounts) < 2 or average == 0:
            return 0.5  # Confianza media por defecto
        
        import statistics
        
        # Calcular coeficiente de variación (CV = desviación estándar / promedio)
        std_dev = statistics.stdev(monthly_amounts)
        cv = std_dev / average if average > 0 else 1
        
        # Convertir CV a confianza (CV bajo = alta confianza)
        # CV < 0.2 = muy confiable (0.9-1.0)
        # CV 0.2-0.5 = confiable (0.7-0.9)
        # CV 0.5-1.0 = moderado (0.5-0.7)
        # CV > 1.0 = poco confiable (0.3-0.5)
        
        if cv < 0.2:
            confidence = 0.9 + (0.2 - cv) * 0.5  # 0.9 a 1.0
        elif cv < 0.5:
            confidence = 0.7 + (0.5 - cv) * 0.67  # 0.7 a 0.9
        elif cv < 1.0:
            confidence = 0.5 + (1.0 - cv) * 0.4  # 0.5 a 0.7
        else:
            confidence = max(0.3, 1.0 / (1.0 + cv))  # 0.3 a 0.5
        
        return min(1.0, max(0.0, confidence))
    
    @classmethod
    def _get_confidence_level(cls, confidence_value):
        """Convertir valor de confianza numérico a nivel descriptivo"""
        if confidence_value >= 0.8:
            return 'high'
        elif confidence_value >= 0.6:
            return 'medium'
        else:
            return 'low'
    
    @classmethod
    def _calculate_weighted_category_average(cls, category_name, start_date, end_date):
        """Calcular promedio ponderado para una categoría (más peso a meses recientes)"""
        from finances.models import Expense, Category
        from django.db.models import Sum
        from decimal import Decimal
        
        try:
            category = Category.objects.get(name=category_name)
        except Category.DoesNotExist:
            return Decimal('0')
        
        weights = cls._calculate_time_weights()
        weighted_sum = Decimal('0')
        
        # Calcular total por mes y aplicar peso
        current_date = start_date
        month_index = 0
        
        while current_date <= end_date:
            # Calcular último día del mes
            if current_date.month == 12:
                month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
            
            # Gastos de este mes para esta categoría
            month_expenses = Expense.objects.filter(
                category=category,
                date__range=[current_date, month_end]
            )
            month_total = month_expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
            
            # Aplicar peso (más peso a meses recientes)
            weighted_sum += month_total * Decimal(str(weights[month_index]))
            
            # Siguiente mes
            current_date = (current_date + relativedelta(months=1)).replace(day=1)
            month_index += 1
        
        return weighted_sum
    
    @classmethod
    def _calculate_category_based_estimate(cls, user, target_month, return_breakdown=False):
        """
        Calcular estimación mejorada basada en categorías recurrentes
        Usa promedio ponderado para categorías variables y promedio simple para fijas
        
        Args:
            return_breakdown: Si True, retorna dict con desglose por categoría
        """
        from finances.models import Expense
        from decimal import Decimal
        
        start_date, end_date = cls._get_last_6_complete_months_range()
        categories_config = cls._get_recurrent_categories_config()
        
        total_estimate = Decimal('0')
        category_breakdown = {}
        
        # 1. Categorías fijas mensuales: Promedio simple (más predecibles)
        monthly_fixed_cats = categories_config['monthly_fixed']
        category_averages = cls._calculate_category_monthly_averages(start_date, end_date)
        
        for cat_name in monthly_fixed_cats:
            if cat_name in category_averages:
                cat_avg = Decimal(str(category_averages[cat_name]['monthly_average']))
                total_estimate += cat_avg
                category_breakdown[cat_name] = {
                    'amount': float(cat_avg),
                    'type': 'monthly_fixed',
                    'trend': category_averages[cat_name].get('trend', {}),
                    'confidence': category_averages[cat_name].get('confidence', 0.5),
                    'confidence_level': category_averages[cat_name].get('confidence_level', 'medium'),
                }
        
        # 2. Categorías variables: Promedio ponderado (más peso a meses recientes)
        variable_cats = categories_config['variable_recurrent']
        for cat_name in variable_cats:
            weighted_avg = cls._calculate_weighted_category_average(cat_name, start_date, end_date)
            total_estimate += weighted_avg
            
            if cat_name in category_averages:
                category_breakdown[cat_name] = {
                    'amount': float(weighted_avg),
                    'type': 'variable_recurrent',
                    'trend': category_averages[cat_name].get('trend', {}),
                    'confidence': category_averages[cat_name].get('confidence', 0.5),
                    'confidence_level': category_averages[cat_name].get('confidence_level', 'medium'),
                }
        
        # 3. Otras categorías (no recurrentes): Promedio general simple
        all_expenses = Expense.objects.filter(date__range=[start_date, end_date])
        recurrent_expenses_total = Decimal('0')
        
        for cat_name in monthly_fixed_cats + variable_cats:
            if cat_name in category_averages:
                recurrent_expenses_total += Decimal(str(category_averages[cat_name]['total_amount']))
        
        total_all_expenses = all_expenses.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        other_expenses_total = total_all_expenses - recurrent_expenses_total
        other_monthly_avg = other_expenses_total / Decimal('6')
        
        total_estimate += other_monthly_avg
        
        if return_breakdown:
            category_breakdown['Otros'] = {
                'amount': float(other_monthly_avg),
                'type': 'other',
                'trend': {'direction': 'stable', 'percentage': 0},
                'confidence': 0.5,
                'confidence_level': 'medium',
            }
            return {
                'total_estimate': float(total_estimate),
                'category_breakdown': category_breakdown,
                'detected_categories': cls._auto_detect_recurrent_categories(),
            }
        
        return float(total_estimate)
    
    @classmethod
    def _calculate_average_total_last_6_months(cls, user, target_month):
        """
        Calcular el promedio de gastos REALES TOTALES de los últimos 6 meses completos desde HOY
        Usa el nuevo método mejorado basado en categorías para mayor precisión
        
        Estrategia:
        - Categorías fijas (Luz, Gas, Internet, Agua): Promedio simple mensual
        - Categorías variables (Supermercado, Combustible): Promedio ponderado (más peso a meses recientes)
        - Otras categorías: Promedio general simple
        """
        try:
            # Usar el nuevo método mejorado basado en categorías
            return cls._calculate_category_based_estimate(user, target_month)
        except Exception as e:
            # Fallback al método simple si hay algún error
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error en cálculo mejorado por categorías, usando método simple: {e}")
            
            from finances.models import Expense
            start_date, end_date = cls._get_last_6_complete_months_range()
            
            all_expenses = Expense.objects.filter(
                date__range=[start_date, end_date]
            )
            
            total_amount = all_expenses.aggregate(
                total=models.Sum('amount'))['total'] or 0
            
            return total_amount / 6

    @classmethod
    def _generate_future_month(cls, user, month_date):
        """Generar datos para un mes futuro - cálculo en tiempo real"""
        from finances.models import Expense
        from subscriptions.models import Subscription
        from .models import ExpenseForecast

        # 1. GASTOS REALES PROGRAMADOS PARA ESE MES FUTURO:
        # a) Suscripciones del mes: gastos ya generados con subscription (hogar)
        real_subscriptions = Expense.objects.filter(
            date__year=month_date.year,
            date__month=month_date.month,
            is_credit=False,
            subscription__isnull=False,
        ).aggregate(total=models.Sum('amount'))['total'] or 0

        # b) Cuotas de créditos programadas para ese mes (gastos reales con fecha específica)
        # IMPORTANTE: Buscar TODAS las cuotas de créditos que están programadas para ese mes
        # Esto incluye cuotas futuras que ya fueron creadas al generar el crédito
        credit_installments = Expense.objects.filter(
            date__year=month_date.year,
            date__month=month_date.month,
            is_credit=True
        )
        real_credit_installments = credit_installments.aggregate(
            total=models.Sum('amount'))['total'] or 0

        # c) Otros gastos reales programados para ese mes (no créditos, no suscripciones)
        # Esto incluye gastos que fueron creados directamente con fecha futura
        other_expenses = Expense.objects.filter(
            date__year=month_date.year,
            date__month=month_date.month,
            is_credit=False,
            subscription__isnull=True
        )
        real_other_expenses = other_expenses.aggregate(
            total=models.Sum('amount'))['total'] or 0

        # Total de gastos REALES programados para ese mes futuro
        # (suscripciones + cuotas de créditos + otros gastos programados)
        real_total = real_subscriptions + real_credit_installments + real_other_expenses

        # 2. ESTIMADO: Promedio de gastos REALES TOTALES de los últimos 6 meses completos
        # Este promedio se calcula desde HOY hacia atrás (tiempo real)
        avg_total_last_6_months = cls._calculate_average_total_last_6_months(user, month_date)
        
        # 3. ESTIMADO DINÁMICO: Promedio MENOS los gastos reales programados para ese mes
        # La estimación es la diferencia entre el promedio esperado y lo que ya está programado
        estimated_amount = max(float(avg_total_last_6_months) - float(real_total), 0)
        
        # El total estimado del mes = gastos reales programados + estimación
        # = real_total + (promedio - real_total) = promedio (si real_total < promedio)
        # Si real_total >= promedio, entonces estimated_amount = 0 y total = real_total
        total_estimated = float(real_total) + estimated_amount

        # Crear o actualizar el registro
        forecast, created = cls.objects.get_or_create(
            user=user,
            month=month_date,
            defaults={
                'future_real_subscriptions': real_subscriptions,
                'future_real_credits': real_credit_installments,  # Cuotas de créditos programadas
                'future_estimated_credits': 0,  # No usamos más este campo
                'future_estimated_other': estimated_amount,  # Estimado dinámico = promedio - gastos reales
                'future_real_total': real_total,  # Total real = suscripciones + cuotas + otros gastos programados
                'future_estimated_total': total_estimated  # Total = real + estimado = promedio (si real < promedio)
            }
        )

        if not created:
            forecast.future_real_subscriptions = real_subscriptions
            forecast.future_real_credits = real_credit_installments
            forecast.future_estimated_credits = 0
            forecast.future_estimated_other = estimated_amount
            forecast.future_real_total = real_total
            forecast.future_estimated_total = total_estimated
            forecast.save()
    
    @classmethod
    def _calculate_monthly_estimate(cls, user, month_date):
        """Calcular estimación mensual basada en suscripciones, créditos y estimaciones activas"""
        from subscriptions.models import Subscription
        from .models import ExpenseForecast

        # Suscripciones activas
        subscriptions = Subscription.objects.filter(user=user, status='active')
        subscriptions_total = sum(sub.get_monthly_amount() for sub in subscriptions)

        # Créditos del mes
        from finances.models import Expense
        credits = Expense.objects.filter(
            user=user,
            is_credit=True,
            date__year=month_date.year,
            date__month=month_date.month
        )
        credits_total = credits.aggregate(
            total=models.Sum('amount'))['total'] or 0

        # Estimaciones activas
        estimates = ExpenseForecast.objects.filter(user=user, is_active=True)
        estimates_total = sum(est.get_monthly_amount() for est in estimates)

        return subscriptions_total + credits_total + estimates_total
    
    def get_total_actual(self):
        """Obtener total real del mes"""
        return self.actual_subscriptions + self.actual_credits + self.actual_other_expenses

    def get_total_projected(self):
        """Obtener total proyectado del mes"""
        if self.future_estimated_total > 0:
            return self.future_estimated_total
        elif self.current_month_estimated > 0:
            return self.current_month_estimated
        else:
            return self.get_total_actual()

    def get_accuracy_percentage(self):
        """Obtener porcentaje de precisión (solo para meses completos)"""
        if self.current_month_estimated > 0:
            return ((self.current_month_actual / self.current_month_estimated) * 100)
        return 0
