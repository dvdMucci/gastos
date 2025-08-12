from django.core.management.base import BaseCommand
from finances.models import Category, PaymentMethod
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Pobla la base de datos con categorías y métodos de pago iniciales'

    def handle(self, *args, **options):
        self.stdout.write('Poblando categorías de gastos...')
        
        # Categorías de gastos
        categories_data = [
            # Alimentación
            {'name': 'Carnicería', 'icon': 'fas fa-drumstick-bite', 'color': '#e74c3c'},
            {'name': 'Verdulería', 'icon': 'fas fa-carrot', 'color': '#27ae60'},
            {'name': 'Supermercado', 'icon': 'fas fa-shopping-cart', 'color': '#3498db'},
            {'name': 'Panadería', 'icon': 'fas fa-bread-slice', 'color': '#f39c12'},
            
            # Hogar
            {'name': 'Ferretería', 'icon': 'fas fa-hammer', 'color': '#8e44ad'},
            {'name': 'Limpieza', 'icon': 'fas fa-broom', 'color': '#1abc9c'},
            {'name': 'Jardín', 'icon': 'fas fa-seedling', 'color': '#2ecc71'},
            
            # Salud
            {'name': 'Medicamentos', 'icon': 'fas fa-pills', 'color': '#e74c3c'},
            {'name': 'Consultas Médicas', 'icon': 'fas fa-user-md', 'color': '#3498db'},
            {'name': 'Estudios Médicos', 'icon': 'fas fa-stethoscope', 'color': '#9b59b6'},
            
            # Transporte
            {'name': 'Combustible', 'icon': 'fas fa-gas-pump', 'color': '#f39c12'},
            {'name': 'Transporte Público', 'icon': 'fas fa-bus', 'color': '#e67e22'},
            {'name': 'Mantenimiento Auto', 'icon': 'fas fa-car', 'color': '#34495e'},
            
            # Entretenimiento
            {'name': 'Salidas', 'icon': 'fas fa-utensils', 'color': '#e91e63'},
            {'name': 'Regalos', 'icon': 'fas fa-gift', 'color': '#ff5722'},
            {'name': 'Hobbies', 'icon': 'fas fa-gamepad', 'color': '#9c27b0'},
            
            # Servicios
            {'name': 'Luz', 'icon': 'fas fa-bolt', 'color': '#ffeb3b'},
            {'name': 'Gas', 'icon': 'fas fa-fire', 'color': '#ff9800'},
            {'name': 'Agua', 'icon': 'fas fa-tint', 'color': '#2196f3'},
            {'name': 'Internet', 'icon': 'fas fa-wifi', 'color': '#00bcd4'},
            {'name': 'Teléfono', 'icon': 'fas fa-phone', 'color': '#4caf50'},
            
            # Educación
            {'name': 'Cursos', 'icon': 'fas fa-graduation-cap', 'color': '#3f51b5'},
            {'name': 'Libros', 'icon': 'fas fa-book', 'color': '#795548'},
            {'name': 'Material Escolar', 'icon': 'fas fa-pencil-alt', 'color': '#607d8b'},
            
            # Tecnología
            {'name': 'Electrodomésticos', 'icon': 'fas fa-tv', 'color': '#673ab7'},
            {'name': 'Electrónica', 'icon': 'fas fa-mobile-alt', 'color': '#ff4081'},
            {'name': 'Software', 'icon': 'fas fa-laptop-code', 'color': '#00bcd4'},
            
            # Reparaciones
            {'name': 'Reparaciones Casa', 'icon': 'fas fa-home', 'color': '#8bc34a'},
            {'name': 'Reparaciones Auto', 'icon': 'fas fa-wrench', 'color': '#ff5722'},
            {'name': 'Reparaciones Electrodomésticos', 'icon': 'fas fa-tools', 'color': '#607d8b'},
            
            # Otros
            {'name': 'Imprevistos', 'icon': 'fas fa-exclamation-triangle', 'color': '#f44336'},
            {'name': 'Donaciones', 'icon': 'fas fa-heart', 'color': '#e91e63'},
            {'name': 'Otros', 'icon': 'fas fa-ellipsis-h', 'color': '#9e9e9e'},
        ]
        
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  ✓ Categoría creada: {category.name}')
            else:
                self.stdout.write(f'  - Categoría ya existe: {category.name}')
        
        self.stdout.write('Poblando métodos de pago...')
        
        # Métodos de pago
        payment_methods_data = [
            {'name': 'Efectivo', 'icon': 'fas fa-money-bill-wave'},
            {'name': 'Débito', 'icon': 'fas fa-credit-card'},
            {'name': 'Crédito', 'icon': 'fas fa-credit-card'},
            {'name': 'Transferencia', 'icon': 'fas fa-exchange-alt'},
            {'name': 'Mercado Pago', 'icon': 'fab fa-cc-mastercard'},
            {'name': 'Ualá', 'icon': 'fas fa-mobile-alt'},
            {'name': 'Lemon', 'icon': 'fas fa-lemon'},
            {'name': 'Otros', 'icon': 'fas fa-ellipsis-h'},
        ]
        
        for pm_data in payment_methods_data:
            payment_method, created = PaymentMethod.objects.get_or_create(
                name=pm_data['name'],
                defaults={'icon': pm_data['icon']}
            )
            if created:
                self.stdout.write(f'  ✓ Método de pago creado: {payment_method.name}')
            else:
                self.stdout.write(f'  - Método de pago ya existe: {payment_method.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Completado! Se crearon {Category.objects.count()} categorías y {PaymentMethod.objects.count()} métodos de pago.'
            )
        )
