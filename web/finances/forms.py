from django import forms
from django.core.exceptions import ValidationError
from .models import Expense, Category, PaymentMethod

class ExpenseForm(forms.ModelForm):
    """Formulario para crear/editar gastos"""
    
    class Meta:
        model = Expense
        fields = [
            'date', 'name', 'amount', 'category', 'payment_method', 
            'payment_type', 'description', 'other_payment_method',
            'is_credit', 'total_credit_amount', 'installments'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del gasto'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'payment_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción opcional'}),
            'other_payment_method': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Especificar método de pago'}),
            'is_credit': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'total_credit_amount': forms.NumberInput(attrs={'class': 'form-control credit-field', 'step': '0.01', 'min': '0'}),
            'installments': forms.NumberInput(attrs={'class': 'form-control credit-field', 'min': '1', 'max': '60'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer campos de crédito opcionales inicialmente
        self.fields['total_credit_amount'].required = False
        self.fields['installments'].required = False
        
        # Agregar clases CSS para campos de crédito
        if self.instance.pk and self.instance.is_credit:
            self.fields['total_credit_amount'].widget.attrs['class'] += ' credit-field'
            self.fields['installments'].widget.attrs['class'] += ' credit-field'
    
    def clean(self):
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')
        is_credit = cleaned_data.get('is_credit')
        amount = cleaned_data.get('amount')
        total_credit_amount = cleaned_data.get('total_credit_amount')
        installments = cleaned_data.get('installments')
        other_payment_method = cleaned_data.get('other_payment_method')
        
        # Validar método de pago "Otros"
        if payment_type == 'other' and not other_payment_method:
            raise ValidationError('Debe especificar el método de pago cuando selecciona "Otros"')
        
        # Validar campos de crédito
        if is_credit:
            if not total_credit_amount or total_credit_amount <= 0:
                raise ValidationError('Para pagos a crédito debe especificar el monto total')
            
            if not installments or installments < 1:
                raise ValidationError('Para pagos a crédito debe especificar el número de cuotas')
            
            if installments > 60:
                raise ValidationError('El número máximo de cuotas es 60')
            
            # Para la primera cuota, el monto debe ser 0 o el monto de la cuota
            if amount and amount > 0:
                if amount > total_credit_amount:
                    raise ValidationError('El monto de la cuota no puede ser mayor al monto total del crédito')
        
        return cleaned_data

class ExpenseFilterForm(forms.Form):
    """Formulario para filtrar gastos"""
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label="Todas las categorías",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    payment_type = forms.ChoiceField(
        choices=[('', 'Todos los tipos')] + Expense.PAYMENT_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    is_credit = forms.ChoiceField(
        choices=[('', 'Todos'), ('True', 'Solo crédito'), ('False', 'Sin crédito')],
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
