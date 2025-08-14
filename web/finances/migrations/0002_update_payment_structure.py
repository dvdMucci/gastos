# Generated manually to update payment structure

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0001_initial'),
    ]

    operations = [
        # Crear nuevo modelo PaymentType
        migrations.CreateModel(
            name='PaymentType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[
                    ('efectivo', 'EFECTIVO'),
                    ('mercado_pago', 'MERCADO PAGO'),
                    ('visa_frances', 'VISA FRANCES'),
                    ('visa_bapro', 'VISA BAPRO'),
                    ('visa_macro', 'VISA MACRO'),
                    ('cuenta_dni', 'CUENTA DNI'),
                    ('transferencia_mp', 'MERCADO PAGO'),
                    ('transferencia_frances', 'FRANCES'),
                    ('transferencia_macro', 'MACRO'),
                    ('transferencia_bapro', 'BAPRO'),
                    ('transferencia_cuenta_dni', 'CUENTA DNI'),
                    ('mastercard_frances', 'MASTERCARD FRANCES'),
                    ('visa_frances_credito', 'VISA FRANCES'),
                    ('visa_bapro_credito', 'VISA BAPRO'),
                    ('mercado_pago_credito', 'MERCADO PAGO'),
                ], max_length=50, unique=True, verbose_name='Tipo de Pago')),
                ('payment_method', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='finances.paymentmethod', verbose_name='Método de Pago')),
                ('is_default', models.BooleanField(default=False, verbose_name='Es por defecto')),
            ],
            options={
                'verbose_name': 'Tipo de Pago',
                'verbose_name_plural': 'Tipos de Pago',
                'ordering': ['payment_method', 'name'],
            },
        ),
        
        # Agregar campo credit_group_id a Expense
        migrations.AddField(
            model_name='expense',
            name='credit_group_id',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='ID del grupo de crédito'),
        ),
        
        # Agregar campo payment_type_new como ForeignKey (temporal)
        migrations.AddField(
            model_name='expense',
            name='payment_type_new',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='finances.paymenttype', verbose_name='Tipo de pago (nuevo)'),
        ),
    ]
