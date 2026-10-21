from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0004_weekly_frequency_infinite_help'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='currency',
            field=models.CharField(
                choices=[('ARS', 'Pesos (ARS)'), ('USD', 'Dólares (USD)')],
                default='ARS',
                help_text='Si es USD, el gasto en pesos se estima con la cotización blue y se fija el día de pago.',
                max_length=3,
                verbose_name='Moneda',
            ),
        ),
    ]
