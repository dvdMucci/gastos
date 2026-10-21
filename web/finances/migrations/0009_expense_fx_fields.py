from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0008_expense_finances_ex_user_id_e9b478_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='amount_usd',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Monto USD'
            ),
        ),
        migrations.AddField(
            model_name='expense',
            name='cotizacion_dolar',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Cotización dólar'
            ),
        ),
        migrations.AddField(
            model_name='expense',
            name='fx_locked',
            field=models.BooleanField(
                default=False,
                help_text='True cuando el ARS ya se fijó el día de pago/cierre.',
                verbose_name='Cotización fijada',
            ),
        ),
    ]
