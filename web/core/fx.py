"""Cotización del dólar (dolarapi.com — blue/compra)."""
import logging
from decimal import Decimal

import requests

logger = logging.getLogger(__name__)


def get_dollar_quotation():
    """
    Cotización actual del dólar blue (precio compra).
    Devuelve Decimal o None si la API falla.
    """
    try:
        response = requests.get('https://dolarapi.com/v1/dolares', timeout=10)
        response.raise_for_status()
        data = response.json()
        for rate in data:
            if rate.get('casa') == 'blue':
                compra = rate.get('compra')
                if compra is not None:
                    return Decimal(str(compra))
        logger.warning('dolarapi: no se encontró casa=blue')
    except Exception as e:
        logger.warning('Error obteniendo cotización dólar: %s', e)
    return None


def usd_to_ars(amount_usd, rate=None):
    """Convierte USD a ARS. Si no hay rate, intenta fetch. None si no hay cotización."""
    if amount_usd is None:
        return None
    amount_usd = Decimal(str(amount_usd))
    if rate is None:
        rate = get_dollar_quotation()
    if rate is None:
        return None
    rate = Decimal(str(rate))
    return (amount_usd * rate).quantize(Decimal('0.01'))
