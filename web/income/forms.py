from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Income, IncomeCategory, IncomeSource
from accounts.models import CustomUser


class IncomeForm(forms.ModelForm):
    """Form for creating/editing income entries"""

    class Meta:
        model = Income
        fields = [
            'date', 'amount', 'description', 'category', 'source',
            'is_recurring', 'recurring_frequency'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'source': forms.Select(attrs={'class': 'form-control'}),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'recurring_frequency': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set required fields
        self.fields['amount'].required = True
        self.fields['date'].required = True
        self.fields['category'].required = True
        self.fields['source'].required = True

        # Configure querysets
        self.fields['category'].queryset = IncomeCategory.objects.filter(is_active=True)
        self.fields['source'].queryset = IncomeSource.objects.filter(is_active=True)

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date > timezone.now().date():
            raise ValidationError('No se permiten fechas futuras para ingresos.')
        return date

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise ValidationError('El monto debe ser un valor positivo.')
        return amount

    def clean(self):
        cleaned_data = super().clean()
        is_recurring = cleaned_data.get('is_recurring')
        recurring_frequency = cleaned_data.get('recurring_frequency')

        if is_recurring and not recurring_frequency:
            raise ValidationError('La frecuencia es obligatoria para ingresos recurrentes.')

        if not is_recurring and recurring_frequency:
            raise ValidationError('No indiques frecuencia si el ingreso no es recurrente.')

        return cleaned_data


class IncomeFilterForm(forms.Form):
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Desde'
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Hasta'
    )
    category = forms.ModelChoiceField(
        queryset=IncomeCategory.objects.filter(is_active=True),
        required=False,
        empty_label='Todas las categorías',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Categoría'
    )
    source = forms.ModelChoiceField(
        queryset=IncomeSource.objects.filter(is_active=True),
        required=False,
        empty_label='Todas las fuentes',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Fuente'
    )
    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.all(),
        required=False,
        empty_label='Todos los usuarios',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Usuario'
    )
    is_recurring = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('True', 'Solo recurrentes'),
            ('False', 'Solo únicos')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Recurrente'
    )
    min_amount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Monto mínimo'}),
        label='Monto mínimo'
    )
    max_amount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Monto máximo'}),
        label='Monto máximo'
    )
    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar en descripción'}),
        label='Buscar'
    )
    sort_order = forms.ChoiceField(
        choices=[
            ('newest', 'Más recientes primero'),
            ('oldest', 'Más antiguos primero')
        ],
        required=False,
        initial='newest',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Orden'
    )