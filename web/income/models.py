from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import CustomUser
import requests
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class IncomeCategory(models.Model):
    """Categories for income sources"""
    name = models.CharField(max_length=100, verbose_name="Name")
    icon = models.CharField(max_length=50, default="fas fa-tag", verbose_name="Icon")
    color = models.CharField(max_length=20, default="primary", verbose_name="Color")
    is_active = models.BooleanField(default=True, verbose_name="Active")

    class Meta:
        verbose_name = "Income Category"
        verbose_name_plural = "Income Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class IncomeSource(models.Model):
    """Sources of income"""
    INCOME_SOURCES = [
        ('BZB', 'BZB'),
        ('Brassara', 'Brassara'),
        ('Podersa', 'Podersa'),
        ('Raster', 'Raster'),
        ('LCC', 'LCC'),
        ('Sanatorio', 'Sanatorio'),
        ('Imagenes', 'Imagenes'),
        ('Sanar', 'Sanar'),
    ]

    name = models.CharField(max_length=20, choices=INCOME_SOURCES, unique=True, verbose_name="Source")
    icon = models.CharField(max_length=50, default="fas fa-dollar-sign", verbose_name="Icon")
    color = models.CharField(max_length=20, default="success", verbose_name="Color")
    is_active = models.BooleanField(default=True, verbose_name="Active")

    class Meta:
        verbose_name = "Income Source"
        verbose_name_plural = "Income Sources"
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()


class Income(models.Model):
    """Main model for income entries"""

    RECURRING_FREQUENCIES = [
        ('monthly', 'MONTHLY'),
        ('quarterly', 'QUARTERLY'),
        ('yearly', 'YEARLY'),
    ]

    # Basic fields
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='User')
    date = models.DateField(verbose_name='Date')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Amount')
    description = models.TextField(blank=True, null=True, verbose_name='Description')

    # Dollar quotation fields
    cotizacion_dolar = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Cotizacion Dólar')
    en_dolares = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='En Dolares')

    # Related fields
    category = models.ForeignKey(IncomeCategory, on_delete=models.CASCADE, verbose_name='Category')
    source = models.ForeignKey(IncomeSource, on_delete=models.CASCADE, verbose_name='Source')

    # Recurring fields
    is_recurring = models.BooleanField(default=False, verbose_name='Is Recurring')
    recurring_frequency = models.CharField(
        max_length=20,
        choices=RECURRING_FREQUENCIES,
        blank=True,
        null=True,
        verbose_name='Recurring Frequency'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    class Meta:
        verbose_name = 'Income'
        verbose_name_plural = 'Income'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'is_recurring']),
            models.Index(fields=['date']),
            models.Index(fields=['category']),
            models.Index(fields=['source']),
        ]

    def __str__(self):
        return f"{self.source.name} - ${self.amount} ({self.date})"

    def get_dollar_quotation(self):
        """Fetch current dollar quotation from API"""
        try:
            response = requests.get('https://dolarapi.com/v1/dolares', timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(f"API data: {data}")

            # Find the "blue" dollar rate
            for rate in data:
                if rate.get('casa') == 'blue':
                    compra = rate.get('compra')
                    logger.info(f"compra: {compra}, type: {type(compra)}")
                    if compra is not None:
                        return Decimal(compra)
        except (requests.RequestException, ValueError, KeyError) as e:
            logger.error(f"Error fetching dollar quotation: {e}")
        return None

    def save(self, *args, **kwargs):
        logger.info(f"Save called: amount={self.amount} (type: {type(self.amount)}), cotizacion_dolar={self.cotizacion_dolar} (type: {type(self.cotizacion_dolar)})")

        # Ensure amount is Decimal
        if not isinstance(self.amount, Decimal):
            self.amount = Decimal(self.amount)

        # Fetch dollar quotation if not already set
        if not self.cotizacion_dolar:
            logger.info("Fetching dollar quotation")
            self.cotizacion_dolar = self.get_dollar_quotation()
            logger.info(f"After fetch: cotizacion_dolar={self.cotizacion_dolar} (type: {type(self.cotizacion_dolar)})")

        # Ensure cotizacion_dolar is Decimal
        if self.cotizacion_dolar and not isinstance(self.cotizacion_dolar, Decimal):
            self.cotizacion_dolar = Decimal(self.cotizacion_dolar)

        # Calculate en_dolares if cotizacion_dolar is available
        if self.cotizacion_dolar and self.amount:
            logger.info(f"Calculating en_dolares: {self.amount} / {self.cotizacion_dolar}")
            self.en_dolares = self.amount / self.cotizacion_dolar
            logger.info(f"en_dolares calculated: {self.en_dolares}")

        super().save(*args, **kwargs)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.is_recurring and not self.recurring_frequency:
            raise ValidationError('Recurring frequency is required for recurring income')
        if not self.is_recurring and self.recurring_frequency:
            raise ValidationError('Recurring frequency should not be set for non-recurring income')