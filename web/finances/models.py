from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import calendar

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
    name = models.CharField(max_length=50, verbose_name="Nombre")
    icon = models.CharField(max_length=50, default="fas fa-credit-card", verbose_name="Icono")
    
    class Meta:
        verbose_name = "Método de Pago"
        verbose_name_plural = "Métodos de Pago"
    
    def __str__(self):
        return self.name

class Expense(models.Model):
    """Modelo principal para gastos"""
    PAYMENT_TYPES = [
        ('cash', 'Efectivo'),
        ('debit', 'Débito'),
        ('credit', 'Crédito'),
        ('other', 'Otros'),
    ]
    
    # Campos básicos
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Usuario")
    date = models.DateField(default=timezone.now, verbose_name="Fecha")
    name = models.CharField(max_length=200, verbose_name="Nombre del gasto")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name="Categoría")
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, verbose_name="Método de pago")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, verbose_name="Tipo de pago")
    
    # Campos para crédito
    is_credit = models.BooleanField(default=False, verbose_name="Es crédito")
    total_credit_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Monto total del crédito")
    installments = models.PositiveIntegerField(default=1, verbose_name="Número de cuotas")
    current_installment = models.PositiveIntegerField(default=1, verbose_name="Cuota actual")
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Monto restante")
    
    # Campos adicionales
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")
    other_payment_method = models.CharField(max_length=100, blank=True, null=True, verbose_name="Otro método de pago")
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    
    class Meta:
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        if self.is_credit:
            return f"{self.name} - Cuota {self.current_installment}/{self.installments}"
        return f"{self.name} - ${self.amount}"
    
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
