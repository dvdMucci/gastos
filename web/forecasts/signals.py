"""
Invalidate Redis forecast cache when underlying household data changes.
Dashboard loads then regenerate via MonthlyForecast.ensure_forecasts().
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


def _invalidate_all_forecasts(**kwargs):
    from .models import MonthlyForecast
    MonthlyForecast.invalidate_forecast_cache()


@receiver(post_save, sender='finances.Expense')
@receiver(post_delete, sender='finances.Expense')
def expense_changed(sender, **kwargs):
    _invalidate_all_forecasts()


@receiver(post_save, sender='subscriptions.Subscription')
@receiver(post_delete, sender='subscriptions.Subscription')
def subscription_changed(sender, **kwargs):
    _invalidate_all_forecasts()


@receiver(post_save, sender='forecasts.ExpenseForecast')
@receiver(post_delete, sender='forecasts.ExpenseForecast')
def expense_forecast_changed(sender, **kwargs):
    _invalidate_all_forecasts()
