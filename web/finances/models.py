from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import calendar
from accounts.models import CustomUser

class Category(models.Model):
    """Categorías de gastos predefinidas"""
    name = models.CharField(max_length=100, verbose_name="Nombre")
    icon = models.CharField(max_length=50, default="fas fa-tag", verbose_name="Icono")
    color = models.CharField(max_length=20, default="primary", verbose_name="Color")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class PaymentMethod(models.Model):
    """Métodos de pago disponibles"""
    PAYMENT_METHODS = [
        ('efectivo', 'EFECTIVO'),
        ('debito', 'DEBITO'),
        ('transferencia', 'TRANSFERENCIA'),
        ('credito', 'CREDITO'),
    ]
    
    name = models.CharField(max_length=20, choices=PAYMENT_METHODS, unique=True, verbose_name="Método de Pago")
    icon = models.CharField(max_length=50, default="fas fa-credit-card", verbose_name="Icono")
    
    class Meta:
        verbose_name = "Método de Pago"
        verbose_name_plural = "Métodos de Pago"
        ordering = ['name']
    
    def __str__(self):
        return self.get_name_display()

class PaymentType(models.Model):
    """Tipos de pago específicos para cada método"""
    PAYMENT_TYPES = [
        # Para EFECTIVO
        ('efectivo', 'EFECTIVO'),
        
        # Para DEBITO
        ('mercado_pago', 'MERCADO PAGO'),
        ('visa_frances', 'VISA FRANCES'),
        ('visa_bapro', 'VISA BAPRO'),
        ('visa_macro', 'VISA MACRO'),
        ('cuenta_dni', 'CUENTA DNI'),
        
        # Para TRANSFERENCIA
        ('transferencia_mp', 'MERCADO PAGO'),
        ('transferencia_frances', 'FRANCES'),
        ('transferencia_macro', 'MACRO'),
        ('transferencia_bapro', 'BAPRO'),
        ('transferencia_cuenta_dni', 'CUENTA DNI'),
        
        # Para CREDITO
        ('mastercard_frances', 'MASTERCARD FRANCES'),
        ('visa_frances_credito', 'VISA FRANCES'),
        ('visa_bapro_credito', 'VISA BAPRO'),
        ('mercado_pago_credito', 'MERCADO PAGO'),
    ]
    
    name = models.CharField(max_length=50, choices=PAYMENT_TYPES, unique=True, verbose_name="Tipo de Pago")
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE, verbose_name="Método de Pago")
    is_default = models.BooleanField(default=False, verbose_name="Es por defecto")
    
    class Meta:
        verbose_name = "Tipo de Pago"
        verbose_name_plural = "Tipos de Pago"
        ordering = ['payment_method', 'name']
    
    def __str__(self):
        return self.get_name_display()

class Expense(models.Model):
    """Modelo principal para gastos"""
    
    # Campos básicos
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Usuario')
    date = models.DateField(verbose_name='Fecha')
    name = models.CharField(max_length=200, verbose_name='Nombre del Gasto')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Categoría')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE, verbose_name='Método de Pago')
    payment_type = models.ForeignKey(PaymentType, on_delete=models.CASCADE, verbose_name='Tipo de Pago')
    description = models.TextField(blank=True, null=True, verbose_name='Descripción')
    
    # Campos para créditos
    is_credit = models.BooleanField(default=False, verbose_name='Es un gasto a crédito')
    total_credit_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Monto total del crédito')
    installments = models.PositiveIntegerField(null=True, blank=True, verbose_name='Número de cuotas')
    current_installment = models.PositiveIntegerField(null=True, blank=True, verbose_name='Cuota actual')
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Monto restante')
    credit_group_id = models.CharField(max_length=100, null=True, blank=True, verbose_name='ID del grupo de crédito')
    
    # Campo para suscripciones
    subscription = models.ForeignKey('subscriptions.Subscription', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Suscripción')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')

    class Meta:
        verbose_name = 'Gasto'
        verbose_name_plural = 'Gastos'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.name} - ${self.amount} ({self.date})"

    def save(self, *args, **kwargs):
        # Si es crédito, calcular el monto restante
        if self.is_credit and self.total_credit_amount:
            if self.current_installment == 1:
                # Primera cuota: monto restante = total - primera cuota
                self.remaining_amount = self.total_credit_amount - self.amount
            else:
                # Cuotas siguientes: monto restante = monto restante anterior - cuota actual
                if self.remaining_amount is None:
                    self.remaining_amount = self.total_credit_amount - self.amount
                else:
                    self.remaining_amount -= self.amount
        
        super().save(*args, **kwargs)
    
    def get_remaining_installments(self):
        """Retorna cuántas cuotas faltan"""
        if self.is_credit:
            return self.installments - self.current_installment
        return 0
    
    def is_last_installment(self):
        """Verifica si es la última cuota"""
        return self.current_installment == self.installments
    
    def get_next_installment_date(self):
        """Calcula la fecha de la siguiente cuota"""
        if self.is_credit and not self.is_last_installment():
            # Obtener el primer día del siguiente mes
            if self.date.month == 12:
                next_month = 1
                next_year = self.date.year + 1
            else:
                next_month = self.date.month + 1
                next_year = self.date.year
            
            return datetime(next_year, next_month, 1).date()
        return None
    
    def get_related_credit_expenses(self):
        """Obtener gastos de crédito relacionados"""
        if self.credit_group_id:
            return Expense.objects.filter(credit_group_id=self.credit_group_id).exclude(pk=self.pk).order_by('current_installment')
        return Expense.objects.none()

class MonthlySummary(models.Model):
    """Resumen mensual de gastos por usuario"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Usuario")
    year = models.PositiveIntegerField(verbose_name="Año")
    month = models.PositiveIntegerField(verbose_name="Mes")
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total gastos")
    total_credit_pending = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total crédito pendiente")
    
    class Meta:
        verbose_name = "Resumen Mensual"
        verbose_name_plural = "Resúmenes Mensuales"
        unique_together = ['user', 'year', 'month']
        ordering = ['-year', '-month']
    
    def __str__(self):
        return f"{self.user.username} - {self.month}/{self.year}"
    
    def get_month_name(self):
        """Retorna el nombre del mes"""
        return calendar.month_name[self.month]
