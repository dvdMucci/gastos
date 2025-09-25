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
    
    # Datos futuros proyectados
    projected_subscriptions = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Suscripciones Proyectadas')
    projected_credits = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Créditos Proyectados')
    projected_estimates = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Estimaciones Proyectadas')
    
    # Total proyectado
    total_projected = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Total Proyectado')
    
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
        return f"{self.month.strftime('%B %Y')} - ${self.total_projected:.2f}"
    
    @classmethod
    def generate_forecasts(cls, user, months_back=6, months_forward=12):
        """Generar estimaciones para los meses especificados"""
        from finances.models import Expense
        from subscriptions.models import Subscription
        from .models import ExpenseForecast

        # Create cache key based on user and parameters
        cache_key = f"forecasts_{user.id}_{months_back}_{months_forward}"
        cached_result = None
        try:
            cached_result = cache.get(cache_key)
        except Exception as e:
            # Log the error but continue without cache
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Cache get failed for key {cache_key}: {e}")

        if cached_result is not None:
            return cached_result

        today = timezone.now().date()
        current_month = today.replace(day=1)

        # Generar estimaciones para meses pasados, actual y futuros
        for i in range(-months_back, months_forward + 1):
            if i < 0:
                # Meses pasados
                month_date = (current_month + relativedelta(months=i)).replace(day=1)
                cls._generate_historical_month(user, month_date)
            elif i == 0:
                # Mes actual
                cls._generate_current_month(user, current_month)
            else:
                # Meses futuros
                month_date = (current_month + relativedelta(months=i)).replace(day=1)
                cls._generate_future_month(user, month_date)

        # Cache the result for 10 minutes
        try:
            cache.set(cache_key, True, 600)
        except Exception as e:
            # Log the error but continue without caching
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Cache set failed for key {cache_key}: {e}")
    
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

        expenses = Expense.objects.filter(user=user, date__range=[start_date, end_date])

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
                'actual_other_expenses': other_total,
                'total_projected': subscriptions_total + credits_total + other_total
            }
        )

        if not created:
            forecast.actual_subscriptions = subscriptions_total
            forecast.actual_credits = credits_total
            forecast.actual_other_expenses = other_total
            forecast.total_projected = subscriptions_total + credits_total + other_total
            forecast.save()
    
    @classmethod
    def _generate_current_month(cls, user, month_date):
        """Generar datos para el mes actual"""
        from finances.models import Expense
        from subscriptions.models import Subscription
        from .models import ExpenseForecast

        today = timezone.now().date()
        start_date = month_date
        if month_date.month == 12:
            end_date = month_date.replace(year=month_date.year + 1, month=1) - timedelta(days=1)
        else:
            end_date = month_date.replace(month=month_date.month + 1) - timedelta(days=1)

        # Gastos reales hasta hoy
        actual_expenses = Expense.objects.filter(
            user=user,
            date__range=[start_date, today]
        )
        actual_total = actual_expenses.aggregate(
            total=models.Sum('amount'))['total'] or 0

        # Estimación para el mes completo
        estimated_total = cls._calculate_monthly_estimate(user, month_date)

        # Crear o actualizar el registro
        forecast, created = cls.objects.get_or_create(
            user=user,
            month=month_date,
            defaults={
                'current_month_estimated': estimated_total,
                'current_month_actual': actual_total,
                'total_projected': estimated_total
            }
        )

        if not created:
            forecast.current_month_estimated = estimated_total
            forecast.current_month_actual = actual_total
            forecast.total_projected = estimated_total
            forecast.save()
    
    @classmethod
    def _generate_future_month(cls, user, month_date):
        """Generar datos para un mes futuro"""
        from finances.models import Expense
        from subscriptions.models import Subscription
        from .models import ExpenseForecast

        # Proyecciones de suscripciones
        subscriptions = Subscription.objects.filter(user=user, status='active')
        subscriptions_total = sum(sub.get_monthly_amount() for sub in subscriptions)

        # Proyecciones de créditos - FIXED LOGIC
        # Find all ongoing credit installments
        ongoing_credits = Expense.objects.filter(
            user=user,
            is_credit=True,
            remaining_amount__gt=0
        )

        credits_total = 0
        current_date = timezone.now().date()
        current_month_start = current_date.replace(day=1)

        for credit in ongoing_credits:
            if credit.total_credit_amount and credit.installments and credit.current_installment < credit.installments:
                # Calculate monthly installment amount
                monthly_installment = credit.total_credit_amount / credit.installments
                remaining_installments = credit.installments - credit.current_installment

                # Calculate months from current month to target month
                months_diff = (month_date.year - current_month_start.year) * 12 + (month_date.month - current_month_start.month)

                # If this future month falls within the remaining installments period
                if months_diff >= 0 and months_diff < remaining_installments:
                    credits_total += monthly_installment


        # Proyecciones de estimaciones activas
        estimates = ExpenseForecast.objects.filter(user=user, is_active=True)
        estimates_total = sum(est.get_forecast_for_month(month_date.year, month_date.month) for est in estimates)

        total_projected = subscriptions_total + credits_total + estimates_total

        # Crear o actualizar el registro
        forecast, created = cls.objects.get_or_create(
            user=user,
            month=month_date,
            defaults={
                'projected_subscriptions': subscriptions_total,
                'projected_credits': credits_total,
                'projected_estimates': estimates_total,
                'total_projected': total_projected
            }
        )

        if not created:
            forecast.projected_subscriptions = subscriptions_total
            forecast.projected_credits = credits_total
            forecast.projected_estimates = estimates_total
            forecast.total_projected = total_projected
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
        return self.projected_subscriptions + self.projected_credits + self.projected_estimates
    
    def get_accuracy_percentage(self):
        """Obtener porcentaje de precisión (solo para meses completos)"""
        if self.current_month_estimated > 0:
            return ((self.current_month_actual / self.current_month_estimated) * 100)
        return 0
