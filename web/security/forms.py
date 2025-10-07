from django import forms
from .models import WhitelistedIP

class WhitelistedIPForm(forms.ModelForm):
    class Meta:
        model = WhitelistedIP
        fields = ['ip', 'reason']
        widgets = {
            'ip': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 192.168.1.1'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Razón para agregar esta IP'}),
        }
        labels = {
            'ip': 'Dirección IP',
            'reason': 'Razón',
        }