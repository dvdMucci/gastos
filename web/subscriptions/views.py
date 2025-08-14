from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import calendar
from .models import Subscription
from .forms import SubscriptionForm, SubscriptionFilterForm

@login_required
def subscription_list(request):
    """Lista de suscripciones con filtros y paginación"""
    subscriptions = Subscription.objects.all()
    
    # Aplicar filtros
    form = SubscriptionFilterForm(request.GET)
    if form.is_valid():
        status = form.cleaned_data.get('status')
        frequency = form.cleaned_data.get('frequency')
        category = form.cleaned_data.get('category')
        payment_method = form.cleaned_data.get('payment_method')
        search = form.cleaned_data.get('search')
        sort_order = form.cleaned_data.get('sort_order', 'start_date')
        
        if status:
            subscriptions = subscriptions.filter(status=status)
        if frequency:
            subscriptions = subscriptions.filter(frequency=frequency)
        if category:
            subscriptions = subscriptions.filter(category=category)
        if payment_method:
            subscriptions = subscriptions.filter(payment_method=payment_method)
        if search:
            subscriptions = subscriptions.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        # Aplicar ordenamiento
        subscriptions = subscriptions.order_by(sort_order)
    else:
        # Sin filtros, ordenar por fecha de inicio
        subscriptions = subscriptions.order_by('-start_date')
    
    # Paginación
    paginator = Paginator(subscriptions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_monthly = subscriptions.filter(
        status='active',
        frequency='monthly'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_active = subscriptions.filter(status='active').aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_monthly': total_monthly,
        'total_active': total_active,
    }
    return render(request, 'subscriptions/subscription_list.html', context)

@login_required
def subscription_create(request):
    """Crear nueva suscripción"""
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.user = request.user
            subscription.save()
            
            messages.success(request, 'Suscripción creada correctamente')
            return redirect('subscriptions:subscription_list')
    else:
        form = SubscriptionForm()
    
    context = {
        'form': form,
        'title': 'Crear Nueva Suscripción'
    }
    return render(request, 'subscriptions/subscription_form.html', context)

@login_required
def subscription_edit(request, subscription_id):
    """Editar suscripción existente"""
    subscription = get_object_or_404(Subscription, id=subscription_id)
    
    if request.method == 'POST':
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            messages.success(request, 'Suscripción actualizada correctamente')
            return redirect('subscriptions:subscription_list')
    else:
        form = SubscriptionForm(instance=subscription)
    
    context = {
        'form': form,
        'subscription': subscription,
        'title': f'Editar Suscripción: {subscription.name}'
    }
    return render(request, 'subscriptions/subscription_form.html', context)

@login_required
def subscription_delete(request, subscription_id):
    """Eliminar suscripción"""
    subscription = get_object_or_404(Subscription, id=subscription_id)
    
    if request.method == 'POST':
        subscription.delete()
        messages.success(request, 'Suscripción eliminada correctamente')
        return redirect('subscriptions:subscription_list')
    
    context = {
        'subscription': subscription
    }
    return render(request, 'subscriptions/subscription_confirm_delete.html', context)

@login_required
def subscription_detail(request, subscription_id):
    """Detalle de la suscripción"""
    subscription = get_object_or_404(Subscription, id=subscription_id)
    
    context = {
        'subscription': subscription
    }
    return render(request, 'subscriptions/subscription_detail.html', context)

@login_required
def subscription_advance(request, subscription_id):
    """Avanza la suscripción al siguiente período"""
    subscription = get_object_or_404(Subscription, id=subscription_id)
    
    if request.method == 'POST':
        if subscription.advance_payment():
            messages.success(request, 'Suscripción avanzada al siguiente período')
        else:
            messages.error(request, 'No se pudo avanzar la suscripción')
    
    return redirect('subscriptions:subscription_detail', subscription_id=subscription_id)

@login_required
def subscription_toggle_status(request, subscription_id):
    """Cambia el estado de la suscripción"""
    subscription = get_object_or_404(Subscription, id=subscription_id)
    
    if request.method == 'POST':
        if subscription.status == 'active':
            subscription.status = 'paused'
            messages.success(request, 'Suscripción pausada')
        else:
            subscription.status = 'active'
            messages.success(request, 'Suscripción activada')
        
        subscription.save()
    
    return redirect('subscriptions:subscription_detail', subscription_id=subscription_id)

@login_required
def subscription_dashboard(request):
    """Dashboard de suscripciones con estadísticas"""
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    # Suscripciones activas
    active_subscriptions = Subscription.objects.filter(status='active')
    
    # Total mensual de suscripciones activas
    monthly_total = active_subscriptions.filter(frequency='monthly').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Próximos pagos (próximo mes)
    next_month = current_month + 1 if current_month < 12 else 1
    next_year = current_year if current_month < 12 else current_year + 1
    
    # Calcular próximos pagos basándose en la fecha de inicio y frecuencia
    upcoming_payments = []
    for subscription in active_subscriptions:
        next_payment = subscription.get_next_payment_date()
        if next_payment and next_payment.month == next_month and next_payment.year == next_year:
            upcoming_payments.append(subscription)
    
    upcoming_payments.sort(key=lambda x: x.get_next_payment_date())
    
    # Suscripciones próximas a vencer
    due_soon = []
    for subscription in active_subscriptions:
        if subscription.is_due_soon():
            due_soon.append(subscription)
    
    # Suscripciones vencidas
    overdue = []
    for subscription in active_subscriptions:
        if subscription.is_overdue():
            overdue.append(subscription)
    
    # Historial de últimos 6 meses
    months_data = []
    for i in range(6):
        month = current_month - i
        year = current_year
        if month < 1:
            month += 12
            year -= 1
        
        # Calcular total del mes basándose en la frecuencia y fecha de inicio
        month_total = 0
        for subscription in active_subscriptions:
            if subscription.frequency == 'monthly':
                month_total += subscription.amount
            elif subscription.frequency == 'quarterly' and month % 3 == 1:
                month_total += subscription.amount
            elif subscription.frequency == 'biannual' and month % 6 == 1:
                month_total += subscription.amount
            elif subscription.frequency == 'annual' and month == 1:
                month_total += subscription.amount
        
        months_data.append({
            'month': month,
            'year': year,
            'month_name': calendar.month_name[month][:3],
            'total': month_total
        })
    
    months_data.reverse()
    
    context = {
        'monthly_total': monthly_total,
        'upcoming_payments': upcoming_payments,
        'due_soon': due_soon,
        'overdue': overdue,
        'months_data': months_data,
        'current_month': current_month,
        'current_year': current_year
    }
    return render(request, 'subscriptions/dashboard.html', context)
