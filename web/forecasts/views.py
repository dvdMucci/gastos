from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import calendar
from .models import ExpenseForecast, MonthlyForecast
from .forms import ExpenseForecastForm, ForecastFilterForm

@login_required
def forecast_dashboard(request):
    """Dashboard principal de estimaciones futuras"""
    # Generar estimaciones para los últimos 6 meses y próximos 12 meses
    MonthlyForecast.generate_forecasts(months_back=6, months_forward=12)
    
    # Obtener estimaciones mensuales
    monthly_forecasts = MonthlyForecast.objects.all().order_by('month')
    
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
    
    # Preparar datos para el gráfico
    chart_labels = []
    subscriptions_data = []
    credits_data = []
    estimates_data = []
    other_data = []
    
    for forecast in monthly_forecasts:
        month_name = forecast.month.strftime('%b %Y')
        chart_labels.append(month_name)
        
        # Datos históricos
        if forecast.actual_subscriptions or forecast.actual_credits or forecast.actual_other_expenses:
            subscriptions_data.append(float(forecast.actual_subscriptions or 0))
            credits_data.append(float(forecast.actual_credits or 0))
            estimates_data.append(0)  # No hay estimaciones en datos históricos
            other_data.append(float(forecast.actual_other_expenses or 0))
        # Mes actual
        elif forecast.current_month_estimated or forecast.current_month_actual:
            subscriptions_data.append(float(forecast.current_month_estimated or 0))
            credits_data.append(0)
            estimates_data.append(0)
            other_data.append(0)
        # Meses futuros
        else:
            subscriptions_data.append(float(forecast.projected_subscriptions or 0))
            credits_data.append(float(forecast.projected_credits or 0))
            estimates_data.append(float(forecast.projected_estimates or 0))
            other_data.append(0)
    
    context = {
        'monthly_forecasts': monthly_forecasts,
        'active_forecasts': active_forecasts,
        'automatic_suggestions': automatic_suggestions,
        'total_projected': total_projected,
        'total_subscriptions': total_subscriptions,
        'total_credits': total_credits,
        'total_estimates': total_estimates,
        'chart_labels': chart_labels,
        'subscriptions_data': subscriptions_data,
        'credits_data': credits_data,
        'estimates_data': estimates_data,
        'other_data': other_data,
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
