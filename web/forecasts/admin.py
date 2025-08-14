# forecasts/admin.py

from django.contrib import admin
from .models import ExpenseForecast, MonthlyForecast

@admin.register(ExpenseForecast)
class ExpenseForecastAdmin(admin.ModelAdmin):
    # ... (tu configuración actual) ...
    pass

@admin.register(MonthlyForecast)
class MonthlyForecastAdmin(admin.ModelAdmin):
    list_display = ['get_month_display', 'total_projected', 'projected_subscriptions', 'projected_credits', 'projected_estimates']
    
    # Usa solo el nombre del campo de fecha. Django creará un filtro por jerarquía (por año, mes, etc.)
    list_filter = ['month'] 
    
    ordering = ['-month']
    
    readonly_fields = ['projected_subscriptions', 'projected_credits', 'projected_estimates', 'total_projected']
    
    def get_month_display(self, obj):
        return obj.month.strftime('%Y-%m')
    get_month_display.short_description = 'Mes'

    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False