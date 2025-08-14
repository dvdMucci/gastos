from django import forms
from django.core.exceptions import ValidationError
from .models import Expense, Category, PaymentMethod, PaymentType
from accounts.models import CustomUser

class ExpenseForm(forms.ModelForm):
    """Formulario para crear/editar gastos"""
    
    class Meta:
        model = Expense
        fields = [
            'name', 'amount', 'date', 'category', 'payment_method', 
            'payment_type', 'description', 'is_credit', 'total_credit_amount', 'installments'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control', 'id': 'id_payment_method'}),
            'payment_type': forms.Select(attrs={'class': 'form-control', 'id': 'id_payment_type', 'style': 'display: none;'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_credit': forms.HiddenInput(),
            'total_credit_amount': forms.HiddenInput(),
            'installments': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ocultar campos de crédito inicialmente
        self.fields['is_credit'].widget = forms.HiddenInput()
        self.fields['total_credit_amount'].widget = forms.HiddenInput()
        self.fields['installments'].widget = forms.HiddenInput()
        
        # Configurar choices para payment_method
        self.fields['payment_method'].choices = [
            ('', 'Seleccione un método de pago'),
            ('efectivo', 'EFECTIVO'),
            ('debito', 'DEBITO'),
            ('transferencia', 'TRANSFERENCIA'),
            ('credito', 'CREDITO'),
        ]

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        payment_type = cleaned_data.get('payment_type')
        is_credit = cleaned_data.get('is_credit')
        amount = cleaned_data.get('amount')
        total_credit_amount = cleaned_data.get('total_credit_amount')
        installments = cleaned_data.get('installments')
        
        # Validar que el tipo de pago corresponda al método
        if payment_method and payment_type:
            if payment_type.payment_method != payment_method:
                raise ValidationError('El tipo de pago seleccionado no corresponde al método de pago')
        
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
        queryset=Category.objects.all(),
        required=False,
        empty_label='Todas las categorías',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Categoría'
    )
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.all(),
        required=False,
        empty_label='Todos los métodos',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Método de Pago'
    )
    payment_type = forms.ModelChoiceField(
        queryset=PaymentType.objects.all(),
        required=False,
        empty_label='Todos los tipos',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Tipo de Pago'
    )
    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.all(),
        required=False,
        empty_label='Todos los usuarios',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Usuario'
    )
    is_credit = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('True', 'Solo créditos'),
            ('False', 'Solo contado')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Crédito'
    )
    min_amount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Monto mínimo'}),
        label='Monto Mínimo'
    )
    max_amount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Monto máximo'}),
        label='Monto Máximo'
    )
    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar en nombre o descripción'}),
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
