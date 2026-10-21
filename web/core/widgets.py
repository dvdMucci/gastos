"""Widgets reutilizables."""
from django import forms


HTML5_DATE_FORMAT = '%Y-%m-%d'


class Html5DateInput(forms.DateInput):
    """
    <input type=\"date\"> exige valor en YYYY-MM-DD.
    Con LANGUAGE_CODE=es, Django puede renderizar dd/mm/yyyy y el navegador
    deja el campo en blanco al editar.
    """

    format_key = 'DATE_INPUT_FORMATS'

    def __init__(self, attrs=None, format=None):
        default_attrs = {
            'type': 'date',
            'class': 'form-control',
            'autocomplete': 'off',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs, format=format or HTML5_DATE_FORMAT)

    def format_value(self, value):
        if value is None or value == '':
            return ''
        if hasattr(value, 'strftime'):
            return value.strftime(self.format or HTML5_DATE_FORMAT)
        return str(value)


def configure_html5_date_fields(form, *field_names):
    """Asegura formato ISO en campos fecha de un form (create/edit/filtros)."""
    for name in field_names:
        field = form.fields.get(name)
        if field is None:
            continue
        field.localize = False
        field.input_formats = [HTML5_DATE_FORMAT, '%d/%m/%Y', '%d/%m/%y']
        if not isinstance(field.widget, Html5DateInput):
            attrs = field.widget.attrs.copy() if field.widget else {}
            attrs.setdefault('type', 'date')
            attrs.setdefault('class', 'form-control')
            field.widget = Html5DateInput(attrs=attrs)
        else:
            field.widget.format = HTML5_DATE_FORMAT
