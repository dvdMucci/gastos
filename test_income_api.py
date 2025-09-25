#!/usr/bin/env python
import os
import django
import sys

# Add the web directory to the Python path
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from income.models import Income, IncomeCategory, IncomeSource
from accounts.models import CustomUser
from datetime import date

# Get the admin user
user = CustomUser.objects.get(username='admin')

# Get a category and source
category = IncomeCategory.objects.first()
source = IncomeSource.objects.first()

# Create a test income
income = Income.objects.create(
    user=user,
    date=date.today(),
    amount=1000.00,
    description='Test income for API integration',
    category=category,
    source=source
)

print(f"Created income: {income}")
print(f"Cotizacion Dolar: {income.cotizacion_dolar}")
print(f"En Dolares: {income.en_dolares}")