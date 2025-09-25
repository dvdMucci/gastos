#!/usr/bin/env python
import os
import django
import sys

# Add the web directory to the Python path
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from income.models import Income

# Test the get_dollar_quotation method
income = Income()
quotation = income.get_dollar_quotation()
print(f"Dollar quotation: {quotation}")

if quotation:
    print("API integration works correctly")
else:
    print("API integration failed or returned None")