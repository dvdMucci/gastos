from django.contrib import admin
from .models import Income, IncomeCategory, IncomeSource


@admin.register(IncomeCategory)
class IncomeCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    ordering = ['name']


@admin.register(IncomeSource)
class IncomeSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ['date', 'user', 'source', 'amount', 'cotizacion_dolar', 'en_dolares', 'category', 'is_recurring']
    list_filter = ['date', 'category', 'source', 'is_recurring', 'user']
    search_fields = ['description', 'user__username', 'source__name']
    ordering = ['-date']
    date_hierarchy = 'date'

    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'date', 'amount', 'description')
        }),
        ('Dollar Information', {
            'fields': ('cotizacion_dolar', 'en_dolares'),
            'classes': ('collapse',)
        }),
        ('Categorization', {
            'fields': ('category', 'source')
        }),
        ('Recurring', {
            'fields': ('is_recurring', 'recurring_frequency'),
            'classes': ('collapse',)
        }),
    )