from django.contrib import admin
from .models import Category, PaymentMethod, PaymentType, Expense, MonthlySummary
from django.contrib.auth import get_user_model

User = get_user_model()

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color', 'is_active']
    list_filter = ['is_active', 'color']
    search_fields = ['name']
    ordering = ['name']

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']
    search_fields = ['name']
    ordering = ['name']

@admin.register(PaymentType)
class PaymentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'payment_method', 'is_default']
    list_filter = ['payment_method', 'is_default']
    search_fields = ['name']
    ordering = ['payment_method', 'name']

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'date', 'amount', 'category', 'payment_method', 'payment_type', 'is_credit', 'installments']
    list_filter = ['date', 'category', 'payment_method', 'payment_type', 'is_credit', 'user']
    search_fields = ['name', 'description', 'user__username']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('user', 'date', 'name', 'amount', 'category', 'description')
        }),
        ('Pago', {
            'fields': ('payment_method', 'payment_type')
        }),
        ('Crédito', {
            'fields': ('is_credit', 'total_credit_amount', 'installments', 'current_installment', 'remaining_amount', 'credit_group_id'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'remaining_amount']

@admin.register(MonthlySummary)
class MonthlySummaryAdmin(admin.ModelAdmin):
    list_display = ['user', 'year', 'month', 'total_expenses', 'total_credit_pending']
    list_filter = ['year', 'month', 'user']
    search_fields = ['user__username']
    ordering = ['-year', '-month']
