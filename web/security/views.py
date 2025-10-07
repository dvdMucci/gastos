from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.cache import cache
from django.urls import reverse
from .models import WhitelistedIP
from .forms import WhitelistedIPForm

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def whitelisted_ips(request):
    """
    Vista para mostrar la lista de IPs en lista blanca y agregar nuevas
    """
    if request.method == 'POST':
        form = WhitelistedIPForm(request.POST)
        if form.is_valid():
            whitelisted_ip = form.save(commit=False)
            whitelisted_ip.added_by = request.user
            whitelisted_ip.save()
            messages.success(request, f'IP {whitelisted_ip.ip} agregada a la lista blanca.')
            return redirect('security:whitelisted_ips')
    else:
        form = WhitelistedIPForm()

    whitelisted_ips = WhitelistedIP.objects.all()
    return render(request, 'security/whitelisted_ips.html', {
        'whitelisted_ips': whitelisted_ips,
        'form': form
    })

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def blocked_ips(request):
    """
    Vista para mostrar IPs bloqueadas temporalmente (desde cache)
    """
    # Para simplificar, mostramos una lista vacía ya que
    # las IPs bloqueadas se manejan en cache y no tenemos
    # una forma fácil de listar todas las claves desde Django
    blocked_ips = []

    return render(request, 'security/blocked_ips.html', {
        'blocked_ips': blocked_ips
    })

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def remove_whitelist(request, ip_id):
    """
    Vista para remover una IP de la lista blanca
    """
    if request.method == 'POST':
        ip = get_object_or_404(WhitelistedIP, id=ip_id)
        ip.delete()
        messages.success(request, f'IP {ip.ip} removida de la lista blanca.')
    return redirect('security:whitelisted_ips')

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def unblock_ip(request, ip):
    """
    Vista para desbloquear una IP temporalmente bloqueada
    """
    if request.method == 'POST':
        # Convertir el ID de vuelta a IP (reemplazar _ por .)
        actual_ip = ip.replace('_', '.')
        cache_key = f"blocked_ip_{actual_ip}"
        cache.delete(cache_key)
        messages.success(request, f'IP {actual_ip} desbloqueada.')
    return redirect('security:blocked_ips')

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def whitelist_ip(request, ip):
    """
    Vista para agregar una IP bloqueada a la lista blanca
    """
    if request.method == 'POST':
        # Convertir el ID de vuelta a IP
        actual_ip = ip.replace('_', '.')

        # Remover del cache de bloqueados
        cache_key = f"blocked_ip_{actual_ip}"
        cache.delete(cache_key)

        # Agregar a lista blanca
        WhitelistedIP.objects.create(
            ip=actual_ip,
            added_by=request.user,
            reason='Agregada desde IPs bloqueadas'
        )

        messages.success(request, f'IP {actual_ip} agregada a la lista blanca.')
    return redirect('security:blocked_ips')
