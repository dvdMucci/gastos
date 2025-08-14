# Generated manually to update payment methods

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0002_update_payment_structure'),
    ]

    operations = [
        # Actualizar PaymentMethod para usar choices
        migrations.AlterField(
            model_name='paymentmethod',
            name='name',
            field=models.CharField(choices=[
                ('efectivo', 'EFECTIVO'),
                ('debito', 'DEBITO'),
                ('transferencia', 'TRANSFERENCIA'),
                ('credito', 'CREDITO'),
            ], max_length=20, unique=True, verbose_name='Método de Pago'),
        ),
    ]
