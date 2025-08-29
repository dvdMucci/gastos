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
from .forms import ExpenseForecastForm, ForecastFilterForm

@login_required
def forecast_dashboard(request):
    """Dashboard principal de estimaciones futuras"""
    # Generar estimaciones para los últimos 6 meses y próximos 12 meses
    MonthlyForecast.generate_forecasts(months_back=6, months_forward=12)
    
    # Obtener estimaciones mensuales
    monthly_forecasts = MonthlyForecast.objects.all().order_by('month')
    
    # Debug: mostrar cuántas estimaciones se generaron
    print(f"Se generaron {monthly_forecasts.count()} estimaciones mensuales")
    
    # Obtener estimaciones activas
    active_forecasts = ExpenseForecast.objects.filter(is_active=True)
    
    # Obtener sugerencias automáticas
    automatic_suggestions = ExpenseForecast.objects.filter(
        is_automatic_suggestion=True
    ).order_by('-confidence', 'name')
    
    # Calcular totales
    total_projected = sum(f.total_projected for f in monthly_forecasts if f.total_projected)
    total_subscriptions = sum(f.projected_subscriptions for f in monthly_forecasts if f.projected_subscriptions)
    total_credits = sum(f.projected_credits for f in monthly_forecasts if f.projected_credits)
    total_estimates = sum(f.projected_estimates for f in monthly_forecasts if f.projected_estimates)
    
    # Preparar datos para el gráfico con barras apiladas
    chart_labels = []
    historical_data = []  # Para 6 meses pasados
    projected_data = []   # Para 12 meses futuros
    current_month_real = []  # Mes actual - datos reales
    current_month_projected = []  # Mes actual - datos proyectados
    
    # Separar datos por período
    current_date = timezone.now().date()
    current_month = current_date.replace(day=1)
    
    print(f"Fecha actual: {current_date}")
    print(f"Mes actual: {current_month}")
    print(f"Total de estimaciones mensuales: {len(monthly_forecasts)}")
    
    # Usar un set para evitar meses duplicados
    processed_months = set()
    
    for forecast in monthly_forecasts:
        month_name = forecast.month.strftime('%b %Y')
        
        # Evitar meses duplicados
        if month_name in processed_months:
            print(f"  - Mes duplicado omitido: {month_name}")
            continue
            
        processed_months.add(month_name)
        chart_labels.append(month_name)
        
        print(f"Procesando mes: {month_name} - {forecast.month}")
        
        # 6 meses pasados - datos históricos
        if forecast.month < current_month:
            print(f"  - Mes histórico: {month_name}")
            historical_data.append({
                'subscriptions': float(forecast.actual_subscriptions or 0),
                'credits': float(forecast.actual_credits or 0),
                'other': float(forecast.actual_other_expenses or 0)
            })
            projected_data.append(None)  # No hay datos proyectados para meses pasados
            current_month_real.append(None)
            current_month_projected.append(None)
        
        # Mes actual - dos barras separadas
        elif forecast.month == current_month:
            print(f"  - Mes actual: {month_name}")
            print(f"    - actual_subscriptions: {forecast.actual_subscriptions}")
            print(f"    - actual_credits: {forecast.actual_credits}")
            print(f"    - actual_other_expenses: {forecast.actual_other_expenses}")
            print(f"    - projected_subscriptions: {forecast.projected_subscriptions}")
            print(f"    - projected_credits: {forecast.projected_credits}")
            print(f"    - projected_estimates: {forecast.projected_estimates}")
            
            historical_data.append(None)
            projected_data.append(None)
            current_month_real.append({
                'subscriptions': float(forecast.actual_subscriptions or 0),
                'credits': float(forecast.actual_credits or 0),
                'other': float(forecast.actual_other_expenses or 0)
            })
            current_month_projected.append({
                'subscriptions': float(forecast.projected_subscriptions or 0),
                'credits': float(forecast.projected_credits or 0),
                'estimates': float(forecast.projected_estimates or 0)
            })
        
        # 12 meses futuros - datos proyectados
        else:
            print(f"  - Mes futuro: {month_name}")
            historical_data.append(None)
            projected_data.append({
                'subscriptions': float(forecast.projected_subscriptions or 0),
                'credits': float(forecast.projected_credits or 0),
                'estimates': float(forecast.projected_estimates or 0)
            })
            current_month_real.append(None)
            current_month_projected.append(None)
    
    print(f"Labels del gráfico: {chart_labels}")
    print(f"Datos históricos: {historical_data}")
    print(f"Datos proyectados: {projected_data}")
    print(f"Mes actual real: {current_month_real}")
    print(f"Mes actual proyectado: {current_month_projected}")
    
    # Verificar si hay gastos reales para el mes actual
    from finances.models import Expense
    from subscriptions.models import Subscription
    
    current_month_start = current_month
    if current_month.month == 12:
        current_month_end = current_month.replace(year=current_month.year + 1, month=1) - timedelta(days=1)
    else:
        current_month_end = current_month.replace(month=current_month.month + 1) - timedelta(days=1)
    
    current_month_expenses = Expense.objects.filter(date__range=[current_month_start, current_month_end])
    current_month_subscriptions = Subscription.objects.filter(
        start_date__lte=current_month_end,
        end_date__gte=current_month_start
    )
    
    print(f"=== VERIFICACIÓN DE GASTOS DEL MES ACTUAL ===")
    print(f"Período: {current_month_start} a {current_month_end}")
    print(f"Total de gastos encontrados: {current_month_expenses.count()}")
    print(f"Total de suscripciones activas: {current_month_subscriptions.count()}")
    
    if current_month_expenses.exists():
        print("Gastos del mes actual:")
        for expense in current_month_expenses[:5]:  # Mostrar solo los primeros 5
            print(f"  - {expense.date}: ${expense.amount} - {expense.description}")
        if current_month_expenses.count() > 5:
            print(f"  ... y {current_month_expenses.count() - 5} más")
    else:
        print("❌ NO HAY GASTOS REGISTRADOS para el mes actual")
    
    if current_month_subscriptions.exists():
        print("Suscripciones activas del mes actual:")
        for sub in current_month_subscriptions[:5]:  # Mostrar solo las primeras 5
            print(f"  - {sub.name}: ${sub.amount} - {sub.frequency}")
        if current_month_subscriptions.count() > 5:
            print(f"  ... y {current_month_subscriptions.count() - 5} más")
    else:
        print("❌ NO HAY SUSCRIPCIONES ACTIVAS para el mes actual")
    
    print(f"=== FIN VERIFICACIÓN ===")
    
    # Convertir a JSON y verificar que sea válido
    chart_labels_json = json.dumps(chart_labels)
    historical_data_json = json.dumps(historical_data)
    projected_data_json = json.dumps(projected_data)
    current_month_real_json = json.dumps(current_month_real)
    current_month_projected_json = json.dumps(current_month_projected)
    
    print(f"JSON generado:")
    print(f"  - chart_labels: {chart_labels_json}")
    print(f"  - historical_data: {historical_data_json}")
    print(f"  - projected_data: {projected_data_json}")
    print(f"  - current_month_real: {current_month_real_json}")
    print(f"  - current_month_projected: {current_month_projected_json}")
    
    # Verificar que el JSON sea válido
    try:
        json.loads(chart_labels_json)
        json.loads(historical_data_json)
        json.loads(projected_data_json)
        json.loads(current_month_real_json)
        json.loads(current_month_projected_json)
        print("✅ Todos los JSON son válidos")
    except json.JSONDecodeError as e:
        print(f"❌ Error en JSON: {e}")
        return render(request, 'forecasts/dashboard.html', {'error': 'Error generando datos del gráfico'})
    
    context = {
        'monthly_forecasts': monthly_forecasts,
        'active_forecasts': active_forecasts,
        'automatic_suggestions': automatic_suggestions,
        'total_projected': total_projected,
        'total_subscriptions': total_subscriptions,
        'total_credits': total_credits,
        'total_estimates': total_estimates,
        'chart_labels': chart_labels_json,
        'historical_data': historical_data_json,
        'projected_data': projected_data_json,
        'current_month_real': current_month_real_json,
        'current_month_projected': current_month_projected_json,
    }
    
    print(f"Context enviado al template:")
    print(f"  - monthly_forecasts: {len(monthly_forecasts)}")
    print(f"  - chart_labels: {len(chart_labels)}")
    print(f"  - historical_data: {len(historical_data)}")
    print(f"  - projected_data: {len(projected_data)}")
    print(f"  - current_month_real: {len(current_month_real)}")
    print(f"  - current_month_projected: {len(current_month_projected)}")
    
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
            MonthlyForecast.generate_forecasts(months_back=6, months_forward=12)
            
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
            MonthlyForecast.generate_forecasts(months_back=6, months_forward=12)
            
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
        MonthlyForecast.generate_forecasts(months_back=6, months_forward=12)
        
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
def monthly_forecasts(request):
    """Vista detallada de estimaciones mensuales"""
    # Generar estimaciones si no existen
    MonthlyForecast.generate_forecasts(months_back=6, months_forward=12)
    
    # Obtener estimaciones mensuales
    monthly_forecasts = MonthlyForecast.objects.all().order_by('month')
    
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
        MonthlyForecast.generate_forecasts(months_back=months_back, months_forward=months_forward)
        
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
            MonthlyForecast.generate_forecasts(months_back=6, months_forward=12)
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def expense_forecast_list(request):
    """Lista todas las estimaciones de gastos del usuario"""
    # Obtener estimaciones del usuario actual
    forecasts = ExpenseForecast.objects.filter(user=request.user).order_by('-created_at')
    
    # Aplicar filtros
    form = ForecastFilterForm(request.GET)
    if form.is_valid():
        year = form.cleaned_data.get('year')
        month = form.cleaned_data.get('month')
        min_amount = form.cleaned_data.get('min_amount')
        max_amount = form.cleaned_data.get('max_amount')
        expense_type = form.cleaned_data.get('expense_type')
        is_active = form.cleaned_data.get('is_active')
        
        if year:
            forecasts = forecasts.filter(start_date__year=year)
        if month:
            forecasts = forecasts.filter(start_date__month=month)
        if min_amount:
            forecasts = forecasts.filter(amount__gte=min_amount)
        if max_amount:
            forecasts = forecasts.filter(amount__lte=max_amount)
        if expense_type:
            forecasts = forecasts.filter(expense_type=expense_type)
        if is_active is not None:
            forecasts = forecasts.filter(is_active=is_active)
    
    # Paginación
    paginator = Paginator(forecasts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_forecasts = forecasts.count()
    active_forecasts = forecasts.filter(is_active=True).count()
    total_amount = forecasts.aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_forecasts': total_forecasts,
        'active_forecasts': active_forecasts,
        'total_amount': total_amount,
    }
    return render(request, 'forecasts/forecast_list.html', context)

@login_required
def regenerate_current_month(request):
    """Vista para regenerar estimaciones del mes actual"""
    if request.method == 'POST':
        try:
            from django.db import models
            from finances.models import Expense
            from subscriptions.models import Subscription
            from .models import MonthlyForecast
            
            today = timezone.now().date()
            current_month = today.replace(day=1)
            
            # Calcular fechas del mes actual
            if current_month.month == 12:
                current_month_end = current_month.replace(year=current_month.year + 1, month=1) - timedelta(days=1)
            else:
                current_month_end = current_month.replace(month=current_month.month + 1) - timedelta(days=1)
            
            # Obtener gastos reales del mes actual
            current_month_expenses = Expense.objects.filter(date__range=[current_month, current_month_end])
            current_month_subscriptions = Subscription.objects.filter(
                start_date__lte=current_month_end,
                end_date__gte=current_month
            )
            
            # Calcular totales por tipo
            subscriptions_total = current_month_expenses.filter(subscription__isnull=False).aggregate(
                total=models.Sum('amount'))['total'] or 0
            credits_total = current_month_expenses.filter(is_credit=True).aggregate(
                total=models.Sum('amount'))['total'] or 0
            other_total = current_month_expenses.filter(
                is_credit=False, 
                subscription__isnull=True
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            
            # Calcular total de suscripciones activas
            subscriptions_amount = sum(sub.amount for sub in current_month_subscriptions)
            
            # Crear o actualizar el registro del mes actual
            forecast, created = MonthlyForecast.objects.get_or_create(
                month=current_month,
                defaults={
                    'actual_subscriptions': subscriptions_total,
                    'actual_credits': credits_total,
                    'actual_other_expenses': other_total,
                    'projected_subscriptions': subscriptions_amount,
                    'projected_credits': 0,  # Los créditos se calculan por estimaciones
                    'projected_estimates': 0,  # Las estimaciones se calculan por estimaciones
                    'total_projected': subscriptions_total + credits_total + other_total
                }
            )
            
            if not created:
                forecast.actual_subscriptions = subscriptions_total
                forecast.actual_credits = credits_total
                forecast.actual_other_expenses = other_total
                forecast.projected_subscriptions = subscriptions_amount
                forecast.total_projected = subscriptions_total + credits_total + other_total
                forecast.save()
            
            print(f"✅ Mes actual regenerado: {current_month}")
            print(f"  - Gastos encontrados: {current_month_expenses.count()}")
            print(f"  - Suscripciones activas: {current_month_subscriptions.count()}")
            print(f"  - Total suscripciones: ${subscriptions_total}")
            print(f"  - Total créditos: ${credits_total}")
            print(f"  - Total otros: ${other_total}")
            print(f"  - Total proyectado: ${forecast.total_projected}")
            
            return JsonResponse({
                'success': True,
                'message': 'Mes actual regenerado exitosamente',
                'expenses_count': current_month_expenses.count(),
                'subscriptions_count': current_month_subscriptions.count(),
                'subscriptions_total': float(subscriptions_total),
                'credits_total': float(credits_total),
                'other_total': float(other_total),
                'total_projected': float(forecast.total_projected)
            })
            
        except Exception as e:
            print(f"❌ Error al regenerar mes actual: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    })
