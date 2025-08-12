from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import calendar
from .models import Expense, Category, PaymentMethod, MonthlySummary
from .forms import ExpenseForm, ExpenseFilterForm

@login_required
def expense_list(request):
    """Lista de gastos con filtros y paginación"""
    expenses = Expense.objects.filter(user=request.user)
    
    # Aplicar filtros
    form = ExpenseFilterForm(request.GET)
    if form.is_valid():
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        category = form.cleaned_data.get('category')
        payment_type = form.cleaned_data.get('payment_type')
        is_credit = form.cleaned_data.get('is_credit')
        min_amount = form.cleaned_data.get('min_amount')
        max_amount = form.cleaned_data.get('max_amount')
        
        if date_from:
            expenses = expenses.filter(date__gte=date_from)
        if date_to:
            expenses = expenses.filter(date__lte=date_to)
        if category:
            expenses = expenses.filter(category=category)
        if payment_type:
            expenses = expenses.filter(payment_type=payment_type)
        if is_credit:
            if is_credit == 'True':
                expenses = expenses.filter(is_credit=True)
            elif is_credit == 'False':
                expenses = expenses.filter(is_credit=False)
        if min_amount:
            expenses = expenses.filter(amount__gte=min_amount)
        if max_amount:
            expenses = expenses.filter(amount__lte=max_amount)
    
    # Paginación
    paginator = Paginator(expenses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    total_credit_pending = expenses.filter(is_credit=True).aggregate(total=Sum('remaining_amount'))['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_expenses': total_expenses,
        'total_credit_pending': total_credit_pending,
    }
    return render(request, 'finances/expense_list.html', context)

@login_required
def expense_create(request):
    """Crear nuevo gasto"""
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            
            # Lógica especial para créditos
            if expense.is_credit and expense.total_credit_amount and expense.installments > 1:
                # Primera cuota: monto 0, crear cuotas futuras
                expense.amount = 0
                expense.save()
                
                # Crear cuotas futuras
                amount_per_installment = expense.total_credit_amount / expense.installments
                current_date = expense.date
                
                for i in range(2, expense.installments + 1):
                    # Calcular fecha de la siguiente cuota
                    if current_date.month == 12:
                        next_month = 1
                        next_year = current_date.year + 1
                    else:
                        next_month = current_date.month + 1
                        next_year = current_date.year
                    
                    next_date = datetime(next_year, next_month, 1).date()
                    
                    # Crear cuota futura
                    Expense.objects.create(
                        user=request.user,
                        date=next_date,
                        name=expense.name,
                        amount=amount_per_installment,
                        category=expense.category,
                        payment_method=expense.payment_method,
                        payment_type=expense.payment_type,
                        description=expense.description,
                        other_payment_method=expense.other_payment_method,
                        is_credit=True,
                        total_credit_amount=expense.total_credit_amount,
                        installments=expense.installments,
                        current_installment=i,
                        remaining_amount=expense.total_credit_amount - (amount_per_installment * i)
                    )
                    current_date = next_date
                
                messages.success(request, f'Gasto a crédito creado con {expense.installments} cuotas')
            else:
                expense.save()
                messages.success(request, 'Gasto creado correctamente')
            
            return redirect('finances:expense_list')
    else:
        form = ExpenseForm()
    
    context = {
        'form': form,
        'title': 'Crear Nuevo Gasto'
    }
    return render(request, 'finances/expense_form.html', context)

@login_required
def expense_edit(request, expense_id):
    """Editar gasto existente"""
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gasto actualizado correctamente')
            return redirect('finances:expense_list')
    else:
        form = ExpenseForm(instance=expense)
    
    context = {
        'form': form,
        'expense': expense,
        'title': f'Editar Gasto: {expense.name}'
    }
    return render(request, 'finances/expense_form.html', context)

@login_required
def expense_delete(request, expense_id):
    """Eliminar gasto"""
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Gasto eliminado correctamente')
        return redirect('finances:expense_list')
    
    context = {
        'expense': expense
    }
    return render(request, 'finances/expense_confirm_delete.html', context)

@login_required
def expense_detail(request, expense_id):
    """Detalle del gasto"""
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    
    # Si es crédito, obtener todas las cuotas relacionadas
    related_expenses = []
    if expense.is_credit:
        related_expenses = Expense.objects.filter(
            user=request.user,
            name=expense.name,
            total_credit_amount=expense.total_credit_amount,
            installments=expense.installments
        ).order_by('current_installment')
    
    context = {
        'expense': expense,
        'related_expenses': related_expenses
    }
    return render(request, 'finances/expense_detail.html', context)

@login_required
def dashboard_finances(request):
    """Dashboard financiero con estadísticas"""
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    # Gastos del mes actual
    current_month_expenses = Expense.objects.filter(
        user=request.user,
        date__year=current_year,
        date__month=current_month
    )
    
    # Total del mes
    month_total = current_month_expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    # Gastos por categoría del mes
    expenses_by_category = current_month_expenses.values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Créditos pendientes
    credit_pending = Expense.objects.filter(
        user=request.user,
        is_credit=True
    ).aggregate(total=Sum('remaining_amount'))['total'] or 0
    
    # Próximas cuotas (próximo mes)
    next_month = current_month + 1 if current_month < 12 else 1
    next_year = current_year if current_month < 12 else current_year + 1
    
    upcoming_installments = Expense.objects.filter(
        user=request.user,
        is_credit=True,
        date__year=next_year,
        date__month=next_month
    ).order_by('date')
    
    # Historial de últimos 6 meses
    months_data = []
    for i in range(6):
        month = current_month - i
        year = current_year
        if month < 1:
            month += 12
            year -= 1
        
        month_expenses = Expense.objects.filter(
            user=request.user,
            date__year=year,
            date__month=month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        months_data.append({
            'month': month,
            'year': year,
            'month_name': calendar.month_name[month][:3],
            'total': month_expenses
        })
    
    months_data.reverse()
    
    context = {
        'month_total': month_total,
        'expenses_by_category': expenses_by_category,
        'credit_pending': credit_pending,
        'upcoming_installments': upcoming_installments,
        'months_data': months_data,
        'current_month': current_month,
        'current_year': current_year
    }
    return render(request, 'finances/dashboard.html', context)

@login_required
def export_expenses(request):
    """Exportar gastos a Excel"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from django.http import HttpResponse
    
    # Obtener gastos filtrados
    expenses = Expense.objects.filter(user=request.user)
    
    # Aplicar filtros si existen
    form = ExpenseFilterForm(request.GET)
    if form.is_valid():
        # Aplicar los mismos filtros que en la vista de lista
        pass
    
    # Crear workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Gastos"
    
    # Estilos
    header_font = Font(bold=True)
    header_fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
    
    # Headers
    headers = ['Fecha', 'Nombre', 'Monto', 'Categoría', 'Método de Pago', 'Tipo', 'Es Crédito', 'Cuotas', 'Descripción']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
    
    # Datos
    for row, expense in enumerate(expenses, 2):
        ws.cell(row=row, column=1, value=expense.date.strftime('%d/%m/%Y'))
        ws.cell(row=row, column=2, value=expense.name)
        ws.cell(row=row, column=3, value=float(expense.amount))
        ws.cell(row=row, column=4, value=expense.category.name)
        ws.cell(row=row, column=5, value=expense.payment_method.name)
        ws.cell(row=row, column=6, value=expense.get_payment_type_display())
        ws.cell(row=row, column=7, value='Sí' if expense.is_credit else 'No')
        ws.cell(row=row, column=8, value=f"{expense.current_installment}/{expense.installments}" if expense.is_credit else '')
        ws.cell(row=row, column=9, value=expense.description or '')
    
    # Ajustar ancho de columnas
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Crear respuesta
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=gastos_{timezone.now().strftime("%Y%m%d")}.xlsx'
    
    wb.save(response)
    return response
