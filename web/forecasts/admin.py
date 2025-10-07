# forecasts/admin.py

from django.contrib import admin
from .models import ExpenseForecast, MonthlyForecast

@admin.register(ExpenseForecast)
class ExpenseForecastAdmin(admin.ModelAdmin):
    # ... (tu configuración actual) ...
    pass

@admin.register(MonthlyForecast)
class MonthlyForecastAdmin(admin.ModelAdmin):
    list_display = ['get_month_display', 'get_total_display', 'get_subscriptions_display', 'get_credits_display', 'get_other_display']

    # Usa solo el nombre del campo de fecha. Django creará un filtro por jerarquía (por año, mes, etc.)
    list_filter = ['month']

    ordering = ['-month']

    readonly_fields = ['future_real_subscriptions', 'future_real_credits', 'future_estimated_credits', 'future_estimated_other', 'future_real_total', 'future_estimated_total', 'actual_subscriptions', 'actual_credits', 'actual_other_expenses', 'current_month_estimated', 'current_month_actual']

    def get_month_display(self, obj):
        return obj.month.strftime('%Y-%m')
    get_month_display.short_description = 'Mes'

    def get_total_display(self, obj):
        if obj.future_estimated_total > 0:
            return f"${obj.future_estimated_total:.2f}"
        elif obj.current_month_estimated > 0:
            return f"${obj.current_month_estimated:.2f}"
        else:
            return f"${obj.actual_subscriptions + obj.actual_credits + obj.actual_other_expenses:.2f}"
    get_total_display.short_description = 'Total'

    def get_subscriptions_display(self, obj):
        if obj.future_real_subscriptions > 0:
            return f"${obj.future_real_subscriptions:.2f}"
        else:
            return f"${obj.actual_subscriptions:.2f}"
    get_subscriptions_display.short_description = 'Suscripciones'

    def get_credits_display(self, obj):
        if obj.future_real_credits > 0:
            return f"${obj.future_real_credits:.2f} (+${obj.future_estimated_credits:.2f})"
        else:
            return f"${obj.actual_credits:.2f}"
    get_credits_display.short_description = 'Créditos'

    def get_other_display(self, obj):
        if obj.future_estimated_other > 0:
            return f"${obj.future_estimated_other:.2f}"
        else:
            return f"${obj.actual_other_expenses:.2f}"
    get_other_display.short_description = 'Otros'

    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False