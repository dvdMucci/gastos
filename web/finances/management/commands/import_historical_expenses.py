from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
import calendar
import openpyxl
import os
from finances.models import Expense, Category, PaymentMethod, PaymentType

class Command(BaseCommand):
    help = 'Importa gastos históricos desde un archivo Excel'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='/gastos/Gastos-Telegram.XLSX',
            help='Ruta al archivo Excel con gastos históricos'
        )
        parser.add_argument(
            '--user',
            type=str,
            default='admin',
            help='Usuario que será asignado a los gastos importados'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        username = options['user']
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'❌ Archivo no encontrado: {file_path}')
            )
            return
        
        # Obtener usuario
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Usuario no encontrado: {username}')
            )
            return
        
        self.stdout.write(f'🔄 Importando gastos para usuario: {user.username}')
        
        # Cargar el archivo Excel
        try:
            workbook = openpyxl.load_workbook(file_path, data_only=True)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al abrir archivo Excel: {e}')
            )
            return
        
        # Mapeo de tipos de pago
        payment_type_mapping = {
            'crédito': 'credito',
            'débito': 'debito', 
            'efectivo': 'efectivo'
        }
        
        # Mapeo inteligente de categorías
        category_mapping = {
            # Alimentos
            'carne': 'Carnicería',
            'pollo': 'Carnicería',
            'fiambre': 'Carnicería',
            'matambre': 'Carnicería',
            'súper': 'Supermercado',
            'super': 'Supermercado',
            'la anonima': 'Supermercado',
            'la anónima': 'Supermercado',
            'la ecologica': 'Supermercado',
            'eden': 'Supermercado',
            'miga': 'Panadería',
            'pan': 'Panadería',
            'papitas': 'Supermercado',
            'chocolate': 'Supermercado',
            'dulce': 'Supermercado',
            'helado': 'Supermercado',
            'empanadas': 'Supermercado',
            'gula': 'Supermercado',
            'jarabe': 'Medicamentos',
            'medicamento': 'Medicamentos',
            'medicina': 'Medicamentos',
            
            # Transporte
            'combustible': 'Combustible',
            'nafta': 'Combustible',
            'gasolina': 'Combustible',
            'seguro': 'Mantenimiento Auto',
            'kangoo': 'Mantenimiento Auto',
            'auto': 'Mantenimiento Auto',
            'coche': 'Mantenimiento Auto',
            
            # Entretenimiento
            'salida': 'Salidas',
            'birreria': 'Salidas',
            'café': 'Salidas',
            'cafe': 'Salidas',
            'cumbal': 'Salidas',
            'baile': 'Cursos',
            'curso': 'Cursos',
            'libro': 'Libros',
            'ingles': 'Cursos',
            'idioma': 'Cursos',
            
            # Hogar
            'aire': 'Electrodomésticos',
            'microondas': 'Electrodomésticos',
            'cortadora': 'Jardín',
            'arbolito': 'Jardín',
            'jardin': 'Jardín',
            'quinta': 'Jardín',
            'red power': 'Electrónica',
            'turbo': 'Electrodomésticos',
            'ventilator': 'Electrodomésticos',
            
            # Ropa
            'ropa': 'Otros',
            'zapatillas': 'Otros',
            'zapas': 'Otros',
            'zapatos': 'Otros',
            'vuelta al cole': 'Material Escolar',
            'escolar': 'Material Escolar',
            'colegio': 'Material Escolar',
        }
        
        total_imported = 0
        total_credits = 0
        
        # Procesar cada hoja (mes)
        for sheet_name in workbook.sheetnames:
            if sheet_name.lower() in ['hoja1', 'sheet1', 'datos']:
                continue  # Saltar hojas genéricas
                
            self.stdout.write(f'📅 Procesando mes: {sheet_name}')
            sheet = workbook[sheet_name]
            
            # Buscar encabezados
            headers = []
            header_row = None
            
            for row_num, row in enumerate(sheet.iter_rows(values_only=True), 1):
                if row and any(cell for cell in row if cell and 'fecha' in str(cell).lower()):
                    headers = [str(cell).lower().strip() if cell else '' for cell in row]
                    header_row = row_num
                    break
            
            if not headers:
                self.stdout.write(f'  ⚠️  No se encontraron encabezados en {sheet_name}')
                continue
            
            # Mapear columnas
            col_mapping = {}
            for i, header in enumerate(headers):
                if 'fecha' in header:
                    col_mapping['fecha'] = i
                elif 'nombre' in header:
                    col_mapping['nombre'] = i
                elif 'valor' in header:
                    col_mapping['valor'] = i
                elif 'tipo' in header:
                    col_mapping['tipo'] = i
                elif 'cuota' in header and 'actual' in header:
                    col_mapping['cuota_actual'] = i
                elif 'cuotas' in header and 'restantes' in header:
                    col_mapping['cuotas_restantes'] = i
            
            if not all(key in col_mapping for key in ['fecha', 'nombre', 'valor', 'tipo']):
                self.stdout.write(f'  ⚠️  Columnas requeridas no encontradas en {sheet_name}')
                continue
            
            # Procesar filas de datos
            for row_num, row in enumerate(sheet.iter_rows(values_only=True, min_row=header_row + 1), header_row + 1):
                if not any(cell for cell in row if cell):
                    continue  # Fila vacía
                
                try:
                    # Extraer datos
                    fecha_str = str(row[col_mapping['fecha']]).strip()
                    nombre = str(row[col_mapping['nombre']]).strip()
                    valor_str = str(row[col_mapping['valor']]).strip()
                    tipo = str(row[col_mapping['tipo']]).strip().lower()
                    
                    # Validar datos básicos
                    if not fecha_str or not nombre or not valor_str or not tipo:
                        continue
                    
                    # Parsear fecha
                    try:
                        if '/' in fecha_str:
                            fecha = datetime.strptime(fecha_str, '%d/%m/%Y').date()
                        else:
                            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                    except ValueError:
                        self.stdout.write(f'    ⚠️  Fecha inválida: {fecha_str}')
                        continue
                    
                    # Parsear valor
                    try:
                        # Limpiar el string de símbolos y espacios
                        valor_str = valor_str.replace('$', '').replace(' ', '').strip()
                        
                        # Si tiene formato de centavos (ej: 170,00)
                        if ',' in valor_str and '.' not in valor_str:
                            # Formato europeo: 170,00 = 170.00
                            valor = float(valor_str.replace(',', '.'))
                        elif ',' in valor_str and '.' in valor_str:
                            # Formato mixto: 1.020,00 = 1020.00
                            parts = valor_str.split(',')
                            if len(parts) == 2 and len(parts[1]) == 2:
                                # Es formato europeo con decimales
                                valor = float(parts[0].replace('.', '') + '.' + parts[1])
                            else:
                                # Otro formato, intentar parsear directamente
                                valor = float(valor_str.replace(',', ''))
                        else:
                            # Sin comas, parsear directamente
                            valor = float(valor_str)
                        
                        # Debug: mostrar valor original y procesado
                        self.stdout.write(f'    💰 Valor: "{row[col_mapping["valor"]]}" -> {valor_str} -> ${valor:.2f}')
                            
                    except ValueError:
                        self.stdout.write(f'    ⚠️  Valor inválido: {valor_str}')
                        continue
                    
                    # Determinar categoría
                    categoria_nombre = 'Otros'  # Por defecto
                    nombre_lower = nombre.lower()
                    
                    for keyword, categoria in category_mapping.items():
                        if keyword in nombre_lower:
                            categoria_nombre = categoria
                            break
                    
                    # Obtener o crear categoría
                    categoria, _ = Category.objects.get_or_create(
                        name=categoria_nombre,
                        defaults={'is_active': True}
                    )
                    
                    # Determinar método de pago
                    if tipo in payment_type_mapping:
                        payment_method_name = payment_type_mapping[tipo]
                        try:
                            payment_method = PaymentMethod.objects.get(name=payment_method_name)
                        except PaymentMethod.DoesNotExist:
                            self.stdout.write(f'    ⚠️  Método de pago no encontrado: {payment_method_name}')
                            continue
                    else:
                        self.stdout.write(f'    ⚠️  Tipo de pago no reconocido: {tipo}')
                        continue
                    
                    # Obtener tipo de pago por defecto
                    try:
                        payment_type = PaymentType.objects.filter(
                            payment_method=payment_method,
                            is_default=True
                        ).first()
                        if not payment_type:
                            payment_type = PaymentType.objects.filter(
                                payment_method=payment_method
                            ).first()
                    except PaymentType.DoesNotExist:
                        self.stdout.write(f'    ⚠️  Tipo de pago no encontrado para: {payment_method_name}')
                        continue
                    
                    # Manejar créditos
                    if tipo == 'crédito':
                        cuota_actual = row[col_mapping.get('cuota_actual', 0)] or 0
                        cuotas_restantes = row[col_mapping.get('cuotas_restantes', 0)] or 0
                        total_cuotas = int(cuota_actual) + int(cuotas_restantes)
                        
                        if total_cuotas > 1:
                            # Crear grupo de crédito
                            import uuid
                            credit_group_id = str(uuid.uuid4())
                            
                            # Primera cuota (cuota 0) con monto 0
                            Expense.objects.create(
                                user=user,
                                date=fecha,
                                name=nombre,
                                amount=0,
                                category=categoria,
                                payment_method=payment_method,
                                payment_type=payment_type,
                                description=f'Importado desde Excel - {sheet_name}',
                                is_credit=True,
                                total_credit_amount=valor,
                                installments=total_cuotas,
                                current_installment=0,
                                remaining_amount=valor,
                                credit_group_id=credit_group_id
                            )
                            
                            # Crear cuotas restantes
                            amount_per_installment = valor / total_cuotas
                            current_date = fecha
                            
                            for i in range(1, total_cuotas + 1):
                                # Calcular siguiente mes
                                if current_date.month == 12:
                                    next_month = 1
                                    next_year = current_date.year + 1
                                else:
                                    next_month = current_date.month + 1
                                    next_year = current_date.year
                                
                                next_date = datetime(next_year, next_month, 1).date()
                                
                                Expense.objects.create(
                                    user=user,
                                    date=next_date,
                                    name=nombre,
                                    amount=amount_per_installment,
                                    category=categoria,
                                    payment_method=payment_method,
                                    payment_type=payment_type,
                                    description=f'Importado desde Excel - {sheet_name} - Cuota {i}',
                                    is_credit=True,
                                    total_credit_amount=valor,
                                    installments=total_cuotas,
                                    current_installment=i,
                                    remaining_amount=valor - (amount_per_installment * i),
                                    credit_group_id=credit_group_id
                                )
                                current_date = next_date
                            
                            total_credits += 1
                            self.stdout.write(f'    ✅ Crédito creado: {nombre} - {total_cuotas} cuotas')
                        else:
                            # Crédito de una sola cuota
                            Expense.objects.create(
                                user=user,
                                date=fecha,
                                name=nombre,
                                amount=valor,
                                category=categoria,
                                payment_method=payment_method,
                                payment_type=payment_type,
                                description=f'Importado desde Excel - {sheet_name}',
                                is_credit=True,
                                total_credit_amount=valor,
                                installments=1,
                                current_installment=1,
                                remaining_amount=0,
                                credit_group_id=None
                            )
                            total_credits += 1
                            self.stdout.write(f'    ✅ Crédito simple: {nombre}')
                    else:
                        # Gasto normal
                        Expense.objects.create(
                            user=user,
                            date=fecha,
                            name=nombre,
                            amount=valor,
                            category=categoria,
                            payment_method=payment_method,
                            payment_type=payment_type,
                            description=f'Importado desde Excel - {sheet_name}',
                            is_credit=False
                        )
                        self.stdout.write(f'    ✅ Gasto: {nombre} - ${valor:.2f}')
                    
                    total_imported += 1
                    
                except Exception as e:
                    self.stdout.write(f'    ❌ Error procesando fila {row_num}: {e}')
                    continue
        
        # Resumen final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Importación completada!\n'
                f'📊 Total de gastos importados: {total_imported}\n'
                f'💳 Total de créditos procesados: {total_credits}\n'
                f'👤 Usuario asignado: {user.username}'
            )
        )
        
        workbook.close()
