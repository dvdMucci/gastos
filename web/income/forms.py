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
            raise ValidationError('Future dates are not allowed for income entries.')
        return date

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise ValidationError('Amount must be a positive value.')
        return amount

    def clean(self):
        cleaned_data = super().clean()
        is_recurring = cleaned_data.get('is_recurring')
        recurring_frequency = cleaned_data.get('recurring_frequency')

        if is_recurring and not recurring_frequency:
            raise ValidationError('Recurring frequency is required for recurring income.')

        if not is_recurring and recurring_frequency:
            raise ValidationError('Recurring frequency should not be set for non-recurring income.')

        return cleaned_data


class IncomeFilterForm(forms.Form):
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='From Date'
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='To Date'
    )
    category = forms.ModelChoiceField(
        queryset=IncomeCategory.objects.filter(is_active=True),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Category'
    )
    source = forms.ModelChoiceField(
        queryset=IncomeSource.objects.filter(is_active=True),
        required=False,
        empty_label='All Sources',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Source'
    )
    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.all(),
        required=False,
        empty_label='All Users',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='User'
    )
    is_recurring = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('True', 'Recurring Only'),
            ('False', 'Non-recurring Only')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Recurring'
    )
    min_amount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Min Amount'}),
        label='Min Amount'
    )
    max_amount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Max Amount'}),
        label='Max Amount'
    )
    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search in description'}),
        label='Search'
    )
    sort_order = forms.ChoiceField(
        choices=[
            ('newest', 'Newest First'),
            ('oldest', 'Oldest First')
        ],
        required=False,
        initial='newest',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Sort Order'
    )