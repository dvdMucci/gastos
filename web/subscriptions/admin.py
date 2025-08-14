# subscriptions/admin.py
from django.contrib import admin
from .models import Subscription

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    # Reemplazar 'next_payment_date' con un método que lo muestre
    list_display = ['name', 'user', 'amount', 'frequency', 'status', 'get_next_payment_date', 'is_active']
    list_filter = ['status', 'frequency', 'category', 'payment_method', 'start_date']
    search_fields = ['name', 'description', 'user__username']
    date_hierarchy = 'start_date'
    
    # El método 'get_next_payment_date' no puede usarse para ordenar directamente. Usaremos un campo de la base de datos.
    ordering = ['start_date', 'name']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('user', 'name', 'description', 'amount')
        }),
        ('Categorización', {
            'fields': ('category', 'payment_method', 'payment_type')
        }),
        ('Frecuencia y Fechas', {
            # 'next_payment_date' es un método, no puede estar en fieldsets
            'fields': ('frequency', 'start_date', 'end_date')
        }),
        ('Estado y Configuración', {
            'fields': ('status', 'auto_create_expense', 'reminder_days')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # 'get_next_payment_date' no puede ser de solo lectura ya que no es un campo de modelo
    readonly_fields = ['created_at', 'updated_at']
    
    # Método para mostrar el estado de actividad de la suscripción
    def is_active(self, obj):
        return obj.status == 'active'
    is_active.boolean = True
    is_active.short_description = 'Activa'

    # Método que llama al método del modelo para mostrar la próxima fecha de pago
    def get_next_payment_date(self, obj):
        return obj.get_next_payment_date()
    get_next_payment_date.short_description = 'Próximo Pago'