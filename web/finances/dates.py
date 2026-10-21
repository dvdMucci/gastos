"""Helpers de fechas de pago (cierre / débito de tarjeta)."""
from datetime import datetime, timedelta


def get_card_payment_monday(year, month):
    """
    Primer lunes del mes con día >= 7.

    Es la regla de fecha de pago/cierre de TC del hogar:
    el lunes no puede caer antes del día 7 (si el primer lunes
    es 1–6, se usa el lunes siguiente).
    """
    first_day = datetime(year, month, 1).date()
    days_to_monday = (0 - first_day.weekday()) % 7  # 0 = lunes
    monday = first_day + timedelta(days=days_to_monday)
    if monday.day < 7:
        monday += timedelta(days=7)
    return monday


# Alias histórico usado en views/serializers
def get_first_monday(year, month):
    return get_card_payment_monday(year, month)
