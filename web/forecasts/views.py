from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import calendar
import json
from .models import ExpenseForecast, MonthlyForecast
from finances.models import Expense
from .forms import ExpenseForecastForm, ForecastFilterForm, ExpenseForecastFilterForm, MonthSelectorForm

@login_required
def forecast_dashboard(request):
    """Dashboard principal de estimaciones futuras"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Forecast dashboard accessed by user: {request.user}")
    # Generar estimaciones para los últimos 6 meses y próximos 12 meses
    MonthlyForecast.generate_forecasts(request.user, months_back=6, months_forward=12)

    # Obtener estimaciones mensuales
    monthly_forecasts = MonthlyForecast.objects.filter(user=request.user).order_by('month')

    # Obtener estimaciones activas con relaciones optimizadas
    active_forecasts = ExpenseForecast.objects.filter(user=request.user, is_active=True).select_related(
        'category', 'payment_method', 'payment_type'
    )

    # Obtener sugerencias automáticas con relaciones optimizadas
    automatic_suggestions = ExpenseForecast.objects.filter(
        user=request.user,
        is_automatic_suggestion=True
    ).select_related(
        'category', 'payment_method', 'payment_type'
    ).order_by('-confidence', 'name')

    # Si no hay parámetros GET, usar valores iniciales del mes actual
    initial_data = {}
    if not request.GET:
        current_date = timezone.now().date()
        initial_data = {
            'year': str(current_date.year),
            'month': str(current_date.month)
        }

    # Manejar formulario de selección de mes
    month_form = MonthSelectorForm(request.GET or None, initial=initial_data)
    selected_month = None
    category_data = []
    category_labels = []

    if month_form.is_valid():
        year = month_form.cleaned_data.get('year')
        month = month_form.cleaned_data.get('month')

        if year and month:
            try:
                selected_month = datetime(int(year), int(month), 1).date()
            except ValueError:
                selected_month = None

    # Si no hay mes seleccionado, usar el mes actual
    if not selected_month:
        selected_month = timezone.now().date().replace(day=1)

    # Preparar datos de categorías para el mes seleccionado
    if selected_month:
        from finances.models import Expense

        # Obtener gastos del mes seleccionado (excluyendo créditos y suscripciones para el breakdown)
        start_date = selected_month
        if selected_month.month == 12:
            end_date = selected_month.replace(year=selected_month.year + 1, month=1) - timedelta(days=1)
        else:
            end_date = selected_month.replace(month=selected_month.month + 1) - timedelta(days=1)

        expenses = Expense.objects.filter(
            user=request.user,
            date__range=[start_date, end_date],
            is_credit=False,
            subscription__isnull=True
        ).select_related('category')

        # Agrupar por categoría
        category_totals = {}
        for expense in expenses:
            category_name = expense.category.name
            if category_name not in category_totals:
                category_totals[category_name] = 0
            category_totals[category_name] += float(expense.amount)

        # Preparar datos para el gráfico
        category_labels = list(category_totals.keys())
        category_data = list(category_totals.values())
    
    # Calcular totales para meses futuros
    current_month = timezone.now().date().replace(day=1)
    future_forecasts = [f for f in monthly_forecasts if f.month > current_month]

    total_projected = sum(f.future_estimated_total for f in future_forecasts if f.future_estimated_total)
    total_subscriptions = sum(f.future_real_subscriptions for f in future_forecasts if f.future_real_subscriptions)
    total_credits = sum((f.future_real_credits or 0) + (f.future_estimated_credits or 0) for f in future_forecasts)
    total_estimates = sum(f.future_estimated_other for f in future_forecasts if f.future_estimated_other)
    
    # Preparar datos para el gráfico según la nueva lógica
    chart_labels = []
    real_data = []  # Gastos reales (contado + crédito + suscripciones)
    estimated_data = []  # Gastos estimados dinámicos
    real_totals_data = []  # Total real
    estimated_totals_data = []  # Total estimado (real + estimado)

    current_month = timezone.now().date().replace(day=1)
    for forecast in monthly_forecasts:
        month_name = forecast.month.strftime('%b %Y')
        chart_labels.append(month_name)

        if forecast.month < current_month:
            # MESES ANTERIORES: Solo gastos reales (contado + crédito + suscripciones)
            real = float((forecast.actual_subscriptions or 0) + (forecast.actual_credits or 0) + (forecast.actual_other_expenses or 0))
            estimated = 0  # No hay estimados en meses pasados
            real_data.append(real)
            estimated_data.append(estimated)
            real_totals_data.append(real)
            estimated_totals_data.append(real)
        elif forecast.month == current_month:
            # MES ACTUAL: Gastos reales hasta hoy + solo la diferencia estimada
            real = float(forecast.current_month_actual or 0)
            estimated_total = float(forecast.current_month_estimated or 0)
            # Solo mostrar la diferencia entre estimado y real
            estimated = max(0, estimated_total - real)
            real_data.append(real)
            estimated_data.append(estimated)
            real_totals_data.append(real)
            estimated_totals_data.append(real + estimated)
        else:
            # MESES FUTUROS: Gastos reales (suscripciones + cuotas) + estimado dinámico
            real = float(forecast.future_real_total or 0)  # Suscripciones + cuotas reales
            estimated = float(forecast.future_estimated_other or 0)  # Estimado dinámico
            real_data.append(real)
            estimated_data.append(estimated)
            real_totals_data.append(real)
            estimated_totals_data.append(real + estimated)
    
    # Preparar valores para el formulario
    selected_year = str(selected_month.year) if selected_month else None
    selected_month_num = str(selected_month.month) if selected_month else None

    logger.info(f"Chart data - Labels: {chart_labels}")
    logger.info(f"Chart data - Real data: {real_data}")
    logger.info(f"Chart data - Estimated data: {estimated_data}")
    logger.info(f"Chart data - Real totals: {real_totals_data}")
    logger.info(f"Chart data - Estimated totals: {estimated_totals_data}")

    context = {
        'monthly_forecasts': monthly_forecasts,
        'active_forecasts': active_forecasts,
        'automatic_suggestions': automatic_suggestions,
        'total_projected': total_projected,
        'total_subscriptions': total_subscriptions,
        'total_credits': total_credits,
        'total_estimates': total_estimates,
        'chart_labels': json.dumps(chart_labels),
        'real_data': json.dumps(real_data),
        'estimated_data': json.dumps(estimated_data),
        'real_totals_data': json.dumps(real_totals_data),
        'estimated_totals_data': json.dumps(estimated_totals_data),
        'month_form': month_form,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'selected_month_num': selected_month_num,
        'category_labels': json.dumps(category_labels),
        'category_data': json.dumps(category_data),
    }
    return render(request, 'forecasts/dashboard.html', context)

@login_required
def expense_forecast_create(request):
    """Crear nueva estimación de gasto"""
    if request.method == 'POST':
        form = ExpenseForecastForm(request.POST)
        if form.is_valid():
            forecast = form.save(commit=False)
            forecast.user = request.user
            forecast.save()

            # Regenerar estimaciones mensuales
            MonthlyForecast.generate_forecasts(request.user, months_back=6, months_forward=12)
            
            messages.success(request, 'Estimación creada correctamente')
            return redirect('forecasts:forecast_dashboard')
    else:
        form = ExpenseForecastForm()
    
    context = {
        'form': form,
        'title': 'Crear Nueva Estimación'
    }
    return render(request, 'forecasts/forecast_form.html', context)

@login_required
def expense_forecast_edit(request, pk):
    """Editar estimación existente"""
    forecast = get_object_or_404(ExpenseForecast, pk=pk)
    
    if request.method == 'POST':
        form = ExpenseForecastForm(request.POST, instance=forecast)
        if form.is_valid():
            form.save()

            # Regenerar estimaciones mensuales
            MonthlyForecast.generate_forecasts(request.user, months_back=6, months_forward=12)
            
            messages.success(request, 'Estimación actualizada correctamente')
            return redirect('forecasts:forecast_dashboard')
    else:
        form = ExpenseForecastForm(instance=forecast)
    
    context = {
        'form': form,
        'forecast': forecast,
        'title': f'Editar Estimación: {forecast.name}'
    }
    return render(request, 'forecasts/forecast_form.html', context)

@login_required
def expense_forecast_delete(request, pk):
    """Eliminar estimación"""
    forecast = get_object_or_404(ExpenseForecast, pk=pk)
    
    if request.method == 'POST':
        forecast.delete()

        # Regenerar estimaciones mensuales
        MonthlyForecast.generate_forecasts(request.user, months_back=6, months_forward=12)
        
        messages.success(request, 'Estimación eliminada correctamente')
        return redirect('forecasts:forecast_dashboard')
    
    context = {
        'forecast': forecast
    }
    return render(request, 'forecasts/forecast_confirm_delete.html', context)

@login_required
def expense_forecast_detail(request, pk):
    """Detalle de la estimación"""
    forecast = get_object_or_404(ExpenseForecast, pk=pk)

    context = {
        'forecast': forecast
    }
    return render(request, 'forecasts/forecast_detail.html', context)

@login_required
def expense_forecast_list(request):
    """Lista de todas las estimaciones del usuario"""
    forecasts = ExpenseForecast.objects.filter(user=request.user).select_related(
        'category', 'payment_method', 'payment_type'
    ).order_by('-created_at')

    # Aplicar filtros
    form = ExpenseForecastFilterForm(request.GET)
    if form.is_valid():
        name = form.cleaned_data.get('name')
        category = form.cleaned_data.get('category')
        is_active = form.cleaned_data.get('is_active')

        if name:
            forecasts = forecasts.filter(name__icontains=name)
        if category:
            forecasts = forecasts.filter(category=category)
        if is_active is not None:
            forecasts = forecasts.filter(is_active=is_active)

    # Paginación
    paginator = Paginator(forecasts, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'form': form,
    }
    return render(request, 'forecasts/forecast_list.html', context)

@login_required
def monthly_forecasts(request):
    """Vista detallada de estimaciones mensuales"""
    # Generar estimaciones si no existen
    MonthlyForecast.generate_forecasts(request.user, months_back=6, months_forward=12)

    # Obtener estimaciones mensuales
    monthly_forecasts = MonthlyForecast.objects.filter(user=request.user).order_by('month')
    
    # Anotar total_projected para filtrado y agregado
    from django.db.models import Case, When, F, DecimalField
    monthly_forecasts = monthly_forecasts.annotate(
        total_projected=Case(
            When(future_estimated_total__gt=0, then=F('future_estimated_total')),
            When(current_month_estimated__gt=0, then=F('current_month_estimated')),
            default=F('actual_subscriptions') + F('actual_credits') + F('actual_other_expenses'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
    )

    # Aplicar filtros
    form = ForecastFilterForm(request.GET)
    if form.is_valid():
        year = form.cleaned_data.get('year')
        month = form.cleaned_data.get('month')
        min_amount = form.cleaned_data.get('min_amount')
        max_amount = form.cleaned_data.get('max_amount')

        if year:
            monthly_forecasts = monthly_forecasts.filter(month__year=year)
        if month:
            monthly_forecasts = monthly_forecasts.filter(month__month=month)
        if min_amount:
            monthly_forecasts = monthly_forecasts.filter(total_projected__gte=min_amount)
        if max_amount:
            monthly_forecasts = monthly_forecasts.filter(total_projected__lte=max_amount)

    # Paginación
    paginator = Paginator(monthly_forecasts, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Estadísticas
    total_projected = monthly_forecasts.aggregate(total=Sum('total_projected'))['total'] or 0
    avg_monthly = total_projected / monthly_forecasts.count() if monthly_forecasts else 0
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_projected': total_projected,
        'avg_monthly': avg_monthly,
    }
    return render(request, 'forecasts/monthly_forecasts.html', context)

@login_required
def generate_forecasts(request):
    """Vista para regenerar estimaciones manualmente"""
    if request.method == 'POST':
        months_back = int(request.POST.get('months_back', 6))
        months_forward = int(request.POST.get('months_forward', 12))

        # Generar estimaciones
        MonthlyForecast.generate_forecasts(request.user, months_back=months_back, months_forward=months_forward)
        
        messages.success(request, f'Estimaciones generadas para {months_back} meses atrás y {months_forward} meses adelante')
        return redirect('forecasts:forecast_dashboard')
    
    return render(request, 'forecasts/generate_forecasts.html')

@login_required
def generate_suggestions(request):
    """Vista para generar sugerencias automáticas"""
    if request.method == 'POST':
        months_back = int(request.POST.get('months_back', 6))
        
        # Generar sugerencias para el usuario actual
        suggestions = ExpenseForecast.generate_automatic_suggestions(request.user, months_back)
        
        messages.success(request, f'Se generaron {len(suggestions)} sugerencias automáticas')
        return redirect('forecasts:forecast_dashboard')
    
    return render(request, 'forecasts/generate_suggestions.html')

@login_required
def activate_suggestion(request, pk):
    """Activar una sugerencia automática"""
    if request.method == 'POST':
        try:
            forecast = get_object_or_404(ExpenseForecast, pk=pk, is_automatic_suggestion=True)
            forecast.is_active = True
            forecast.is_automatic_suggestion = False
            forecast.save()

            # Regenerar estimaciones mensuales
            MonthlyForecast.generate_forecasts(request.user, months_back=6, months_forward=12)
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})
