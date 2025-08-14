from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from finances.models import Category, PaymentMethod, PaymentType
from datetime import datetime, timedelta
import calendar

User = get_user_model()

class Subscription(models.Model):
    FREQUENCY_CHOICES = [
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('biannual', 'Semestral'),
        ('annual', 'Anual'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('paused', 'Pausada'),
        ('cancelled', 'Cancelada'),
        ('expired', 'Expirada'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Nombre')
    description = models.TextField(blank=True, null=True, verbose_name='Descripción')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuario')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Categoría')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE, verbose_name='Método de Pago')
    payment_type = models.ForeignKey(PaymentType, on_delete=models.CASCADE, verbose_name='Tipo de Pago')
    
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly', verbose_name='Frecuencia')
    start_date = models.DateField(verbose_name='Fecha de Inicio')
    end_date = models.DateField(null=True, blank=True, verbose_name='Fecha de Fin')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='Estado')
    auto_create_expense = models.BooleanField(default=True, verbose_name='Crear Gastos Automáticamente')
    reminder_days = models.IntegerField(default=7, verbose_name='Días de Recordatorio')
    
    # Campos para seguimiento de renovación
    last_renewal_date = models.DateField(null=True, blank=True, verbose_name='Última Renovación')
    next_renewal_validation = models.DateField(null=True, blank=True, verbose_name='Próxima Validación de Renovación')
    renewal_reminder_sent = models.BooleanField(default=False, verbose_name='Recordatorio de Renovación Enviado')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')
    
    class Meta:
        verbose_name = 'Suscripción'
        verbose_name_plural = 'Suscripciones'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} - ${self.amount} ({self.get_frequency_display()})"
    
    def save(self, *args, **kwargs):
        # Si es una nueva suscripción o cambió el monto, crear gastos futuros
        if not self.pk or 'amount' in kwargs.get('update_fields', []):
            self._create_future_expenses()
        
        # Calcular próxima validación de renovación (5 años desde la fecha de inicio)
        if not self.next_renewal_validation:
            self.next_renewal_validation = self.start_date + timedelta(days=5*365)
        
        super().save(*args, **kwargs)
    
    def _create_future_expenses(self):
        """Crear gastos futuros hasta 5 años adelante"""
        from finances.models import Expense
        
        # Eliminar gastos futuros existentes si cambió el monto
        if self.pk:
            Expense.objects.filter(
                subscription=self,
                date__gt=timezone.now().date()
            ).delete()
        
        # Crear gastos futuros
        current_date = self.start_date
        end_date = self.start_date + timedelta(days=5*365)  # 5 años
        
        while current_date <= end_date:
            if current_date >= timezone.now().date():
                # Crear gasto para esta fecha
                Expense.objects.create(
                    user=self.user if hasattr(self, 'user') else None,
                    date=current_date,
                    name=self.name,
                    amount=self.amount,
                    category=self.category,
                    payment_method=self.payment_method,
                    payment_type=self.payment_type,
                    description=f"Suscripción: {self.name}",
                    is_credit=False,
                    subscription=self
                )
            
            # Calcular próxima fecha según frecuencia
            if self.frequency == 'monthly':
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            elif self.frequency == 'quarterly':
                if current_date.month >= 10:
                    current_date = current_date.replace(year=current_date.year + 1, month=current_date.month - 9)
                else:
                    current_date = current_date.replace(month=current_date.month + 3)
            elif self.frequency == 'biannual':
                if current_date.month >= 7:
                    current_date = current_date.replace(year=current_date.year + 1, month=current_date.month - 6)
                else:
                    current_date = current_date.replace(month=current_date.month + 6)
            elif self.frequency == 'annual':
                current_date = current_date.replace(year=current_date.year + 1)
    
    def get_next_payment_date(self):
        """Obtener la próxima fecha de pago"""
        if not self.is_active():
            return None
        
        current_date = timezone.now().date()
        next_date = self.start_date
        
        while next_date <= current_date:
            if self.frequency == 'monthly':
                if next_date.month == 12:
                    next_date = next_date.replace(year=next_date.year + 1, month=1)
                else:
                    next_date = next_date.replace(month=next_date.month + 1)
            elif self.frequency == 'quarterly':
                if next_date.month >= 10:
                    next_date = next_date.replace(year=next_date.year + 1, month=next_date.month - 9)
                else:
                    next_date = next_date.replace(month=next_date.month + 3)
            elif self.frequency == 'biannual':
                if next_date.month >= 7:
                    next_date = next_date.replace(year=next_date.year + 1, month=next_date.month - 6)
                else:
                    next_date = next_date.replace(month=next_date.month + 6)
            elif self.frequency == 'annual':
                next_date = next_date.replace(year=next_date.year + 1)
        
        return next_date
    
    def advance_payment(self):
        """Avanzar al siguiente pago"""
        next_date = self.get_next_payment_date()
        if next_date:
            self.start_date = next_date
            self.last_renewal_date = timezone.now().date()
            self.save(update_fields=['start_date', 'last_renewal_date'])
            return True
        return False
    
    def is_active(self):
        """Verificar si la suscripción está activa"""
        return self.status == 'active' and (not self.end_date or self.end_date >= timezone.now().date())
    
    def is_due_soon(self):
        """Verificar si el pago vence pronto"""
        if not self.is_active():
            return False
        
        next_date = self.get_next_payment_date()
        if next_date:
            days_until_due = (next_date - timezone.now().date()).days
            return days_until_due <= self.reminder_days
        return False
    
    def is_overdue(self):
        """Verificar si el pago está vencido"""
        if not self.is_active():
            return False
        
        next_date = self.get_next_payment_date()
        if next_date:
            return next_date < timezone.now().date()
        return False
    
    def get_total_paid(self):
        """Obtener total pagado hasta la fecha"""
        from finances.models import Expense
        return Expense.objects.filter(
            subscription=self,
            date__lte=timezone.now().date()
        ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    def get_remaining_payments(self):
        """Obtener pagos restantes hasta el fin"""
        if not self.end_date:
            return None
        
        total_payments = 0
        current_date = timezone.now().date()
        
        while current_date <= self.end_date:
            if self.frequency == 'monthly':
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            elif self.frequency == 'quarterly':
                if current_date.month >= 10:
                    current_date = current_date.replace(year=current_date.year + 1, month=current_date.month - 9)
                else:
                    current_date = current_date.replace(month=current_date.month + 3)
            elif self.frequency == 'biannual':
                if current_date.month >= 7:
                    current_date = current_date.replace(year=current_date.year + 1, month=current_date.month - 6)
                else:
                    current_date = current_date.replace(month=current_date.month + 6)
            elif self.frequency == 'annual':
                current_date = current_date.replace(year=current_date.year + 1)
            
            total_payments += 1
        
        return total_payments
    
    def needs_renewal_validation(self):
        """Verificar si necesita validación de renovación"""
        if not self.next_renewal_validation:
            return False
        return timezone.now().date() >= self.next_renewal_validation
    
    def mark_renewal_reminder_sent(self):
        """Marcar que se envió el recordatorio de renovación"""
        self.renewal_reminder_sent = True
        self.save(update_fields=['renewal_reminder_sent'])
