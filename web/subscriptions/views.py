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
    from decimal import Decimal
    from core.fx import get_dollar_quotation

    subscriptions = Subscription.objects.select_related(
        'user', 'category', 'payment_method', 'payment_type'
    )

    form = SubscriptionFilterForm(request.GET)
    if form.is_valid():
        status = form.cleaned_data.get('status')
        frequency = form.cleaned_data.get('frequency')
        category = form.cleaned_data.get('category')
        payment_method = form.cleaned_data.get('payment_method')
        currency = form.cleaned_data.get('currency')
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
        if currency:
            subscriptions = subscriptions.filter(currency=currency)
        if search:
            subscriptions = subscriptions.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        subscriptions = subscriptions.order_by(sort_order)
    else:
        subscriptions = subscriptions.order_by('-start_date')

    rate = get_dollar_quotation()
    from core.charts import subscription_category_pie

    # Totales en ARS al día de hoy (solo activas del queryset filtrado)
    total_monthly_ars = Decimal('0.00')
    total_active_ars = Decimal('0.00')
    # Evaluar una sola vez para totales + torta (evita N queries extra)
    subscription_list = list(subscriptions)
    for sub in subscription_list:
        if sub.status != 'active' or not sub.is_active():
            continue
        ars = sub.amount_ars_today(rate=rate)
        total_active_ars += ars
        total_monthly_ars += sub.monthly_ars_equivalent(rate=rate)

    paginator = Paginator(subscription_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Adjuntar display ARS a cada ítem de la página
    for sub in page_obj:
        sub.display_ars = sub.amount_ars_today(rate=rate)

    context = {
        'page_obj': page_obj,
        'form': form,
        'total_monthly': total_monthly_ars,
        'total_active': total_active_ars,
        'dollar_rate': rate,
    }
    context.update(subscription_category_pie(subscription_list, rate=rate))
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
    """Eliminar suscripción (también borra gastos futuros materializados)."""
    subscription = get_object_or_404(Subscription, id=subscription_id)
    
    if request.method == 'POST':
        # Subscription.delete() limpia gastos futuros antes del SET_NULL del FK
        subscription.delete()
        messages.success(request, 'Suscripción y gastos futuros eliminados correctamente')
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
    
    # Total mensual equivalente de suscripciones activas
    monthly_total = 0
    for subscription in active_subscriptions:
        if not subscription.is_active():
            continue
        if subscription.frequency == 'weekly':
            monthly_total += float(subscription.amount) * 4.33
        elif subscription.frequency == 'monthly':
            monthly_total += float(subscription.amount)
        elif subscription.frequency == 'quarterly':
            monthly_total += float(subscription.amount) / 3
        elif subscription.frequency == 'biannual':
            monthly_total += float(subscription.amount) / 6
        elif subscription.frequency == 'annual':
            monthly_total += float(subscription.amount) / 12
    
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
            if subscription.frequency == 'weekly':
                # ~4.3 semanas/mes; usamos 4 para el resumen del dashboard
                month_total += subscription.amount * 4
            elif subscription.frequency == 'monthly':
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

    from core.charts import subscription_category_pie
    from core.fx import get_dollar_quotation
    from decimal import Decimal

    rate = get_dollar_quotation()
    # Total activo en ARS (la plantilla lo muestra; antes faltaba en el context)
    total_active = Decimal('0.00')
    for subscription in active_subscriptions:
        if subscription.is_active():
            total_active += subscription.amount_ars_today(rate=rate)

    # Recalcular monthly_total en ARS (incluye USD)
    monthly_total_ars = Decimal('0.00')
    for subscription in active_subscriptions:
        if subscription.is_active():
            monthly_total_ars += subscription.monthly_ars_equivalent(rate=rate)
    
    context = {
        'monthly_total': monthly_total_ars,
        'total_active': total_active,
        'upcoming_payments': upcoming_payments,
        'due_soon': due_soon,
        'overdue': overdue,
        'months_data': months_data,
        'current_month': current_month,
        'current_year': current_year,
        'next_month': next_month,
        'next_year': next_year,
        'dollar_rate': rate,
    }
    context.update(subscription_category_pie(active_subscriptions, rate=rate))
    return render(request, 'subscriptions/dashboard.html', context)
