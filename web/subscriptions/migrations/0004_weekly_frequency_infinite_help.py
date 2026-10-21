# Generated manually for weekly frequency + infinite subscriptions help text

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0003_alter_subscription_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='frequency',
            field=models.CharField(
                choices=[
                    ('weekly', 'Semanal'),
                    ('monthly', 'Mensual'),
                    ('quarterly', 'Trimestral'),
                    ('biannual', 'Semestral'),
                    ('annual', 'Anual'),
                ],
                default='monthly',
                max_length=20,
                verbose_name='Frecuencia',
            ),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='end_date',
            field=models.DateField(
                blank=True,
                help_text='Vacío = sin caducidad (suscripción infinita).',
                null=True,
                verbose_name='Fecha de Fin',
            ),
        ),
    ]
