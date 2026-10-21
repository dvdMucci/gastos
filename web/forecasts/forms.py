from django import forms
from .models import ExpenseForecast
from finances.models import Category, PaymentMethod, PaymentType
from core.widgets import Html5DateInput
import calendar

class ExpenseForecastForm(forms.ModelForm):
    """Formulario para crear/editar estimaciones de gastos"""
    
    class Meta:
        model = ExpenseForecast
        fields = [
            'name', 'description', 'amount', 'category', 'payment_method', 
            'payment_type', 'expense_type', 'start_date', 'end_date',
            'frequency', 'confidence', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del gasto estimado'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción opcional'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control', 'id': 'id_payment_method'}),
            'payment_type': forms.Select(attrs={'class': 'form-control', 'id': 'id_payment_type'}),
            'expense_type': forms.Select(attrs={'class': 'form-control'}),
            'start_date': Html5DateInput(),
            'end_date': Html5DateInput(),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
            'confidence': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from core.widgets import configure_html5_date_fields
        configure_html5_date_fields(self, 'start_date', 'end_date')
        # Agregar clases CSS para campos de fecha
        if self.instance.pk and self.instance.end_date:
            self.fields['end_date'].widget.attrs['class'] += ' end-date-field'
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        payment_method = cleaned_data.get('payment_method')
        payment_type = cleaned_data.get('payment_type')
        frequency = cleaned_data.get('frequency')
        
        # Validar que la fecha de finalización sea posterior a la de inicio
        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError('La fecha de finalización debe ser posterior a la fecha de inicio')
        
        # Validar que el tipo de pago corresponda al método
        if payment_method and payment_type:
            if payment_type.payment_method != payment_method:
                raise forms.ValidationError('El tipo de pago seleccionado no corresponde al método de pago')
        
        # Validar frecuencia para gastos únicos
        if frequency == 'one_time' and start_date and end_date:
            days_diff = (end_date - start_date).days
            if days_diff > 31:
                raise forms.ValidationError('Para gastos únicos, el período no debe exceder 31 días')
        
        return cleaned_data

class ForecastFilterForm(forms.Form):
    """Formulario para filtrar estimaciones mensuales"""

    year = forms.ChoiceField(
        choices=[('', 'Todos los años')] + [(i, str(i)) for i in range(2024, 2030)],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'onchange': 'this.form.submit()'})
    )
    month = forms.ChoiceField(
        choices=[('', 'Todos los meses')] + [(i, calendar.month_name[i]) for i in range(1, 13)],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    min_amount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Monto mínimo', 'step': '0.01'})
    )
    max_amount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Monto máximo', 'step': '0.01'})
    )

class ExpenseForecastFilterForm(forms.Form):
    """Formulario para filtrar estimaciones de gastos"""

    name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar por nombre'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='Todas las categorías',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    is_active = forms.NullBooleanField(
        required=False,
        widget=forms.Select(choices=[('', 'Todos'), (True, 'Activas'), (False, 'Inactivas')], attrs={'class': 'form-control'})
    )

class MonthSelectorForm(forms.Form):
    """Formulario para seleccionar mes en el dashboard"""

    year = forms.ChoiceField(
        choices=[(str(i), str(i)) for i in range(2015, 2036)],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'year-selector',
            'onchange': 'this.form.submit()'
        }),
        label='Año'
    )
    month = forms.ChoiceField(
        choices=[
            ('1', 'Enero'), ('2', 'Febrero'), ('3', 'Marzo'), ('4', 'Abril'),
            ('5', 'Mayo'), ('6', 'Junio'), ('7', 'Julio'), ('8', 'Agosto'),
            ('9', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'month-selector',
            'onchange': 'this.form.submit()'
        }),
        label='Mes'
    )
