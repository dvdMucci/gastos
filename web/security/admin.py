from django.contrib import admin
from .models import WhitelistedIP

@admin.register(WhitelistedIP)
class WhitelistedIPAdmin(admin.ModelAdmin):
    list_display = ['ip', 'added_by', 'date_added', 'reason']
    list_filter = ['date_added', 'added_by']
    search_fields = ['ip', 'reason']
    readonly_fields = ['date_added']
    ordering = ['-date_added']

    fieldsets = (
        ('Información de IP', {
            'fields': ('ip', 'reason')
        }),
        ('Información del Sistema', {
            'fields': ('added_by', 'date_added'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.added_by = request.user
        super().save_model(request, obj, form, change)
