from django import template
from django.utils import dateformat
from django.utils.translation import gettext as _

register = template.Library()

@register.filter
def spanish_date(value):
    """Formatea una fecha en español"""
    if not value:
        return ""
    
    # Mapeo de días y meses en español
    dias = {
        0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves',
        4: 'Viernes', 5: 'Sábado', 6: 'Domingo'
    }
    
    meses = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    try:
        dia_semana = dias[value.weekday()]
        dia = value.day
        mes = meses[value.month]
        año = value.year
        
        return f"{dia_semana}, {dia} de {mes} de {año}"
    except:
        return value.strftime("%d/%m/%Y")
