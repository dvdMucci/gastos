# Generated manually for finances app

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nombre')),
                ('icon', models.CharField(default='fas fa-tag', max_length=50, verbose_name='Icono')),
                ('color', models.CharField(default='primary', max_length=20, verbose_name='Color')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activa')),
            ],
            options={
                'verbose_name': 'Categoría',
                'verbose_name_plural': 'Categorías',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Nombre')),
                ('icon', models.CharField(default='fas fa-credit-card', max_length=50, verbose_name='Icono')),
            ],
            options={
                'verbose_name': 'Método de Pago',
                'verbose_name_plural': 'Métodos de Pago',
            },
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now, verbose_name='Fecha')),
                ('name', models.CharField(max_length=200, verbose_name='Nombre del gasto')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Monto')),
                ('payment_type', models.CharField(choices=[('cash', 'Efectivo'), ('debit', 'Débito'), ('credit', 'Crédito'), ('other', 'Otros')], max_length=20, verbose_name='Tipo de pago')),
                ('is_credit', models.BooleanField(default=False, verbose_name='Es crédito')),
                ('total_credit_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Monto total del crédito')),
                ('installments', models.PositiveIntegerField(default=1, verbose_name='Número de cuotas')),
                ('current_installment', models.PositiveIntegerField(default=1, verbose_name='Cuota actual')),
                ('remaining_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Monto restante')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Descripción')),
                ('other_payment_method', models.CharField(blank=True, max_length=100, null=True, verbose_name='Otro método de pago')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='finances.category', verbose_name='Categoría')),
                ('payment_method', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='finances.paymentmethod', verbose_name='Método de pago')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.customuser', verbose_name='Usuario')),
            ],
            options={
                'verbose_name': 'Gasto',
                'verbose_name_plural': 'Gastos',
                'ordering': ['-date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MonthlySummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveIntegerField(verbose_name='Año')),
                ('month', models.PositiveIntegerField(verbose_name='Mes')),
                ('total_expenses', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Total gastos')),
                ('total_credit_pending', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Total crédito pendiente')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.customuser', verbose_name='Usuario')),
            ],
            options={
                'verbose_name': 'Resumen Mensual',
                'verbose_name_plural': 'Resúmenes Mensuales',
                'ordering': ['-year', '-month'],
                'unique_together': {('user', 'year', 'month')},
            },
        ),
    ]
