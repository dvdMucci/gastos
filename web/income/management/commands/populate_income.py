from django.core.management.base import BaseCommand
from income.models import IncomeCategory, IncomeSource

class Command(BaseCommand):
    help = 'Pobla la base de datos con categorías y fuentes de ingresos iniciales'

    def handle(self, *args, **options):
        self.stdout.write('Poblando categorías de ingresos...')

        # Categorías de ingresos
        categories_data = [
            {'name': 'Salario', 'icon': 'fas fa-briefcase', 'color': 'success'},
            {'name': 'Freelance', 'icon': 'fas fa-laptop-code', 'color': 'primary'},
            {'name': 'Inversiones', 'icon': 'fas fa-chart-line', 'color': 'info'},
            {'name': 'Alquiler', 'icon': 'fas fa-home', 'color': 'warning'},
            {'name': 'Pensión', 'icon': 'fas fa-user-check', 'color': 'secondary'},
            {'name': 'Bonos', 'icon': 'fas fa-gift', 'color': 'danger'},
            {'name': 'Otros', 'icon': 'fas fa-ellipsis-h', 'color': 'dark'},
        ]

        for cat_data in categories_data:
            category, created = IncomeCategory.objects.get_or_create(
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

        self.stdout.write('Poblando fuentes de ingresos...')

        # Fuentes de ingresos (usando las choices definidas en el modelo)
        sources_data = [
            ('BZB', 'fas fa-building', 'success'),
            ('Brassara', 'fas fa-code', 'primary'),
            ('Podersa', 'fas fa-chart-pie', 'info'),
            ('Raster', 'fas fa-house-user', 'warning'),
            ('LCC', 'fas fa-landmark', 'secondary'),
            ('Sanatorio', 'fas fa-users', 'danger'),
            ('Imagenes', 'fas fa-question-circle', 'dark'),
            ('Sanar', 'fas fa-ellipsis-h', 'light'),
        ]

        for source_name, icon, color in sources_data:
            source, created = IncomeSource.objects.get_or_create(
                name=source_name,
                defaults={
                    'icon': icon,
                    'color': color,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  ✓ Fuente creada: {source.name}')
            else:
                self.stdout.write(f'  - Fuente ya existe: {source.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Completado! Se crearon {IncomeCategory.objects.count()} categorías y {IncomeSource.objects.count()} fuentes de ingresos.'
            )
        )