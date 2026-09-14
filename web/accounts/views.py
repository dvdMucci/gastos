import logging
import secrets

from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.contrib import messages
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods, require_POST
from django.core.paginator import Paginator
from django.db.models import Sum
from django.utils import timezone
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.util import random_hex # No usado directamente en el código provisto, pero útil para OTP
import qrcode
import io
import base64
import pyotp # Necesario para la generación de la URL de configuración, aunque TOTPDevice lo maneja
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .models import CustomUser
from .forms import CustomUserCreationForm, ProfileForm, LoginForm, ChangePasswordForm
from .serializers import UserSerializer
from income.models import Income

# Max password-reset emails per IP per hour (enumeration / spam protection)
PASSWORD_RESET_RATE_LIMIT = 5
PASSWORD_RESET_RATE_WINDOW = 3600

logger = logging.getLogger(__name__)


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST, request=request)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
@require_POST
def logout_view(request):
    """
    Cierra la sesión. Sólo por POST: por GET, cualquier página externa podía
    cerrarle la sesión al usuario con un simple <img src="...">.
    """
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    # Current month and year
    current_month = timezone.now().month
    current_year = timezone.now().year

    # Income statistics for current month
    current_month_incomes = Income.objects.filter(
        user=request.user,
        date__year=current_year,
        date__month=current_month
    )
    month_income_total = current_month_incomes.aggregate(total=Sum('amount'))['total'] or 0

    # Recurring income total (monthly recurring incomes)
    recurring_income_total = Income.objects.filter(
        user=request.user,
        is_recurring=True,
        recurring_frequency='monthly'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Total number of income records
    total_incomes = Income.objects.filter(user=request.user).count()

    context = {
        'user': request.user,
        'user_count': CustomUser.objects.count() if request.user.can_manage_users() else None,
        'month_income_total': month_income_total,
        'recurring_income_total': recurring_income_total,
        'total_incomes': total_incomes,
        'current_month': current_month,
        'current_year': current_year,
    }
    return render(request, 'dashboard.html', context)

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    
    # Obtener dispositivo TOTP
    totp_device = request.user.totpdevice_set.filter(confirmed=True).first()
    
    context = {
        'form': form,
        'totp_device': totp_device,
        'is_2fa_enabled': request.user.is_2fa_enabled,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def setup_2fa(request):
    # Crear o obtener dispositivo TOTP
    device, created = TOTPDevice.objects.get_or_create(
        user=request.user,
        name='default',
        defaults={'confirmed': False}
    )
    
    if not device.confirmed:
        # Generar QR code
        qr_code_url = device.config_url
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_code_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        qr_code_data = base64.b64encode(buffer.getvalue()).decode()
        
        if request.method == 'POST':
            token = request.POST.get('token')
            if device.verify_token(token):
                device.confirmed = True
                device.save()
                request.user.is_2fa_enabled = True
                request.user.save()
                messages.success(request, '2FA configurado correctamente')
                return redirect('profile')
            else:
                messages.error(request, 'Código inválido')
        
        context = {
            'qr_code_data': qr_code_data,
            'secret_key': device.key, # La clave secreta es útil para depuración o si el usuario no puede escanear el QR
        }
        return render(request, 'accounts/setup_2fa.html', context)
    else:
        messages.info(request, '2FA ya está configurado')
        return redirect('profile')

@login_required
def disable_2fa(request):
    if request.method == 'POST':
        request.user.totpdevice_set.all().delete() # Elimina todos los dispositivos 2FA del usuario
        request.user.is_2fa_enabled = False
        request.user.save()
        messages.success(request, '2FA deshabilitado correctamente')
    return redirect('profile')

# Función de ayuda para verificar si el usuario es administrador
def is_admin(user):
    return user.is_authenticated and user.can_manage_users()

@user_passes_test(is_admin) # Decorador para restringir el acceso solo a administradores
def user_list(request):
    users = CustomUser.objects.all().order_by('-date_joined')
    paginator = Paginator(users, 10) # Paginación de 10 usuarios por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'accounts/user_list.html', {'page_obj': page_obj})

@user_passes_test(is_admin)
def user_create(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Usuario {user.username} creado correctamente')
            return redirect('user_list')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Crear Usuario'})

@user_passes_test(is_admin)
def user_edit(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        user_type = request.POST.get('user_type')
        is_active = request.POST.get('is_active') == 'on' # Los checkboxes envían 'on' o nada
        
        if form.is_valid():
            user = form.save(commit=False) # Guarda el formulario pero no en la BD aún
            user.user_type = user_type
            user.is_active = is_active
            user.save() # Ahora guarda en la BD
            messages.success(request, f'Usuario {user.username} actualizado correctamente')
            return redirect('user_list')
    else:
        form = ProfileForm(instance=user)
    
    context = {
        'form': form,
        'user_obj': user,
        'user_types': CustomUser.USER_TYPES, # Pasa los tipos de usuario para el select
        'title': f'Editar Usuario: {user.username}'
    }
    return render(request, 'accounts/user_edit.html', context)

@user_passes_test(is_admin)
@require_http_methods(["POST"]) # Solo permite peticiones POST para eliminar
def user_delete(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if user == request.user:
        messages.error(request, 'No puedes eliminar tu propia cuenta')
    else:
        username = user.username
        user.delete()
        messages.success(request, f'Usuario {username} eliminado correctamente')
    
    return redirect('user_list')

@login_required
def change_password(request):
    if request.method == 'POST':
        # El PasswordChangeForm requiere la instancia del usuario
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Importante: Esto actualiza el hash de autenticación de la sesión del usuario
            # para evitar que se cierre la sesión después de cambiar la contraseña.
            update_session_auth_hash(request, user)
            messages.success(request, 'Tu contraseña ha sido actualizada correctamente.')
            return redirect('profile') # Redirige al perfil o a una página de éxito
        else:
            messages.error(request, 'Por favor, corrige los errores a continuación.')
    else:
        form = ChangePasswordForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form, 'title': 'Cambiar Contraseña'})


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_user_by_telegram_chat_id(request):
    """
    Verifica un usuario por su telegram_chat_id y devuelve su token de API.

    Lo consume el workflow Gastos2 de n8n. Como devuelve una credencial de
    acceso, exige el secreto compartido en el header X-API-Key: sin él,
    cualquiera podría pedir un token probando chat_ids de Telegram.
    """
    expected_secret = getattr(settings, 'N8N_API_SECRET', '')

    if not expected_secret:
        # Sin secreto configurado el endpoint queda cerrado, no abierto.
        logger.error('N8N_API_SECRET no está configurado; se rechaza la petición')
        return Response(
            {'error': 'Endpoint no disponible'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    provided_secret = request.headers.get('X-API-Key', '')

    # compare_digest evita filtrar el secreto por diferencia de tiempos.
    if not secrets.compare_digest(provided_secret, expected_secret):
        logger.warning(
            'Intento de acceso a verify-user sin secreto válido desde %s',
            request.META.get('REMOTE_ADDR', 'desconocido')
        )
        return Response(
            {'error': 'No autorizado'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    telegram_chat_id = request.query_params.get('telegram_chat_id')

    if not telegram_chat_id:
        return Response(
            {'error': 'telegram_chat_id parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = CustomUser.objects.get(telegram_chat_id=telegram_chat_id)
    except CustomUser.DoesNotExist:
        return Response(
            {'error': 'User not found',
             "telegram_chat_id": telegram_chat_id},
            status=status.HTTP_200_OK
        )

    if not user.is_active:
        return Response(
            {'error': 'User not found',
             "telegram_chat_id": telegram_chat_id},
            status=status.HTTP_200_OK
        )

    # Se reutiliza el token existente en lugar de borrarlo y crear uno nuevo:
    # rotarlo en cada llamada invalidaba el token que pudiera estar usando
    # otra ejecución del workflow en paralelo.
    token, _ = Token.objects.get_or_create(user=user)

    data = UserSerializer(user).data
    data['token'] = token.key
    return Response(data)


def _client_ip(request):
    """Best-effort client IP; trusts X-Forwarded-For only behind private proxies."""
    remote_addr = request.META.get('REMOTE_ADDR', '')
    try:
        from ipaddress import ip_address
        ip_obj = ip_address(remote_addr)
        is_private = ip_obj.is_private or ip_obj.is_loopback
    except ValueError:
        is_private = False

    if is_private or remote_addr in getattr(settings, 'TRUSTED_PROXY_IPS', []):
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded:
            return forwarded.split(',')[0].strip()
    return remote_addr or 'unknown'


class RateLimitedPasswordResetView(PasswordResetView):
    """
    Django password reset with per-IP rate limiting.
    Always shows the same success page (does not reveal whether the email exists).
    """
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    html_email_template_name = None

    def form_valid(self, form):
        ip = _client_ip(self.request)
        cache_key = f'pwd_reset_rate_{ip}'
        try:
            count = cache.get(cache_key, 0) or 0
        except Exception:
            count = 0

        if count >= PASSWORD_RESET_RATE_LIMIT:
            # Same UX as success — do not send mail, do not leak rate-limit details
            logger.warning(f'Password reset rate limit hit for IP {ip}')
            return redirect(self.get_success_url())

        try:
            cache.set(cache_key, count + 1, PASSWORD_RESET_RATE_WINDOW)
        except Exception:
            pass

        return super().form_valid(form)


class AppPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class AppPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


class AppPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'
