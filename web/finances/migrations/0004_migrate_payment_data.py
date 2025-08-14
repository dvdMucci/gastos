# Generated manually to migrate payment data

from django.db import migrations

def migrate_payment_methods(apps, schema_editor):
    PaymentMethod = apps.get_model('finances', 'PaymentMethod')
    PaymentType = apps.get_model('finances', 'PaymentType')
    
    # Crear los nuevos métodos de pago
    efectivo, _ = PaymentMethod.objects.get_or_create(
        name='efectivo',
        defaults={'icon': 'fas fa-money-bill-wave'}
    )
    
    debito, _ = PaymentMethod.objects.get_or_create(
        name='debito',
        defaults={'icon': 'fas fa-credit-card'}
    )
    
    transferencia, _ = PaymentMethod.objects.get_or_create(
        name='transferencia',
        defaults={'icon': 'fas fa-exchange-alt'}
    )
    
    credito, _ = PaymentMethod.objects.get_or_create(
        name='credito',
        defaults={'icon': 'fas fa-credit-card'}
    )
    
    # Crear los tipos de pago
    PaymentType.objects.get_or_create(
        name='efectivo',
        defaults={
            'payment_method': efectivo,
            'is_default': True
        }
    )
    
    # Para DEBITO
    PaymentType.objects.get_or_create(
        name='mercado_pago',
        defaults={
            'payment_method': debito,
            'is_default': True
        }
    )
    PaymentType.objects.get_or_create(
        name='visa_frances',
        defaults={
            'payment_method': debito,
            'is_default': False
        }
    )
    PaymentType.objects.get_or_create(
        name='visa_bapro',
        defaults={
            'payment_method': debito,
            'is_default': False
        }
    )
    PaymentType.objects.get_or_create(
        name='visa_macro',
        defaults={
            'payment_method': debito,
            'is_default': False
        }
    )
    PaymentType.objects.get_or_create(
        name='cuenta_dni',
        defaults={
            'payment_method': debito,
            'is_default': False
        }
    )
    
    # Para TRANSFERENCIA
    PaymentType.objects.get_or_create(
        name='transferencia_mp',
        defaults={
            'payment_method': transferencia,
            'is_default': True
        }
    )
    PaymentType.objects.get_or_create(
        name='transferencia_frances',
        defaults={
            'payment_method': transferencia,
            'is_default': False
        }
    )
    PaymentType.objects.get_or_create(
        name='transferencia_macro',
        defaults={
            'payment_method': transferencia,
            'is_default': False
        }
    )
    PaymentType.objects.get_or_create(
        name='transferencia_bapro',
        defaults={
            'payment_method': transferencia,
            'is_default': False
        }
    )
    PaymentType.objects.get_or_create(
        name='transferencia_cuenta_dni',
        defaults={
            'payment_method': transferencia,
            'is_default': False
        }
    )
    
    # Para CREDITO
    PaymentType.objects.get_or_create(
        name='mastercard_frances',
        defaults={
            'payment_method': credito,
            'is_default': True
        }
    )
    PaymentType.objects.get_or_create(
        name='visa_frances_credito',
        defaults={
            'payment_method': credito,
            'is_default': False
        }
    )
    PaymentType.objects.get_or_create(
        name='visa_bapro_credito',
        defaults={
            'payment_method': credito,
            'is_default': False
        }
    )
    PaymentType.objects.get_or_create(
        name='mercado_pago_credito',
        defaults={
            'payment_method': credito,
            'is_default': False
        }
    )

def reverse_migrate_payment_methods(apps, schema_editor):
    PaymentType = apps.get_model('finances', 'PaymentType')
    PaymentType.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0003_update_payment_methods'),
    ]

    operations = [
        migrations.RunPython(migrate_payment_methods, reverse_migrate_payment_methods),
    ]
