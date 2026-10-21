from django import forms
from .models import Subscription
from finances.models import Category, PaymentMethod, PaymentType
from core.widgets import Html5DateInput

class SubscriptionForm(forms.ModelForm):
    """Formulario para crear/editar suscripciones"""
    
    class Meta:
        model = Subscription
        fields = [
            'name', 'description', 'amount', 'currency', 'category', 'payment_method',
            'payment_type', 'frequency', 'start_date', 'end_date',
            'status', 'auto_create_expense', 'reminder_days'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la suscripción'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción opcional'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control', 'id': 'id_payment_method'}),
            'payment_type': forms.Select(attrs={'class': 'form-control', 'id': 'id_payment_type'}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
            'start_date': Html5DateInput(),
            'end_date': Html5DateInput(attrs={
                'title': 'Vacío = sin caducidad (infinita)',
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'auto_create_expense': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'reminder_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '30'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from core.widgets import configure_html5_date_fields
        configure_html5_date_fields(self, 'start_date', 'end_date')
        # Fecha de fin opcional = suscripción infinita
        self.fields['end_date'].required = False
        self.fields['end_date'].help_text = (
            'Dejar vacío = sin caducidad (infinita). '
            'Los gastos se generan a 12 meses vista y el job los va extendiendo.'
        )
        self.fields['currency'].help_text = (
            'USD: el gasto en pesos se estima con el blue y se fija el día de pago '
            '(TC: primer lunes ≥ día 7 del mes siguiente; efectivo: fecha del período).'
        )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        payment_method = cleaned_data.get('payment_method')
        payment_type = cleaned_data.get('payment_type')
        
        # Validar que la fecha de finalización sea posterior a la de inicio
        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError('La fecha de finalización debe ser posterior a la fecha de inicio')
        
        # Validar que el tipo de pago corresponda al método
        if payment_method and payment_type:
            if payment_type.payment_method != payment_method:
                raise forms.ValidationError('El tipo de pago seleccionado no corresponde al método de pago')
        
        return cleaned_data

class SubscriptionFilterForm(forms.Form):
    """Formulario para filtrar suscripciones"""
    
    status = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + Subscription.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    frequency = forms.ChoiceField(
        choices=[('', 'Todas las frecuencias')] + Subscription.FREQUENCY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="Todas las categorías",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.all(),
        required=False,
        empty_label="Todos los métodos",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    currency = forms.ChoiceField(
        choices=[('', 'Todas las monedas'), ('ARS', 'Pesos (ARS)'), ('USD', 'Dólares (USD)')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Moneda',
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Buscar en nombre o descripción...'
        })
    )
    sort_order = forms.ChoiceField(
        choices=[
            ('start_date', 'Fecha de inicio'),
            ('-start_date', 'Fecha de inicio (descendente)'),
            ('name', 'Nombre'),
            ('-name', 'Nombre (descendente)'),
            ('amount', 'Monto'),
            ('-amount', 'Monto (descendente)'),
        ],
        initial='start_date',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
