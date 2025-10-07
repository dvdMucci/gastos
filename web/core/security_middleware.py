import logging
import time
from django.http import HttpResponseForbidden, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.conf import settings
import ipaddress
from security.models import WhitelistedIP

logger = logging.getLogger(__name__)

class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware de seguridad para detectar y bloquear intentos de ataque
    """
    
    # Rutas sospechosas que intentan los bots
    SUSPICIOUS_PATHS = [
        '/wordpress/',
        '/wp-admin/',
        '/wp-login.php',
        '/wp-content/',
        '/administrator/',
        '/admin.php',
        '/phpmyadmin/',
        '/.env',
        '/config.php',
        '/xmlrpc.php',
        '/.git/',
        '/backup/',
        '/test/',
        '/debug/',
        '/api/v1/',
        '/swagger/',
        '/.well-known/',
        '/robots.txt',
        '/sitemap.xml',
        '/favicon.ico',
    ]
    
    # User agents sospechosos
    SUSPICIOUS_USER_AGENTS = [
        'sqlmap',
        'nikto',
        'nmap',
        'masscan',
        'zap',
        'burp',
        'scanner',
        'bot',
        'crawler',
        'spider',
        'scraper',
        'curl',
        'wget',
        'python-requests',
        'java/',
        'go-http',
    ]
    
    def process_request(self, request):
        """
        Procesa cada request para detectar actividad sospechosa
        """
        client_ip = self.get_client_ip(request)

        # Verificar si la IP está en lista blanca
        if self.is_ip_whitelisted(client_ip):
            return None

        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        path = request.path.lower()

        # Detectar intentos de acceso a rutas sospechosas
        if self.is_suspicious_path(path):
            self.log_suspicious_activity(
                request, 
                f"Intento de acceso a ruta sospechosa: {path}",
                "SUSPICIOUS_PATH"
            )
            
            # Bloquear IP temporalmente
            self.block_ip_temporarily(client_ip, 3600)  # 1 hora
            
            return HttpResponseForbidden(
                "Acceso denegado por razones de seguridad",
                content_type="text/plain"
            )
        
        # Detectar user agents sospechosos
        if self.is_suspicious_user_agent(user_agent):
            self.log_suspicious_activity(
                request,
                f"User agent sospechoso: {user_agent}",
                "SUSPICIOUS_USER_AGENT"
            )
            
            # Bloquear IP temporalmente
            self.block_ip_temporarily(client_ip, 1800)  # 30 minutos
            
            return HttpResponseForbidden(
                "Acceso denegado por razones de seguridad",
                content_type="text/plain"
            )
        
        # Verificar si la IP está bloqueada
        if self.is_ip_blocked(client_ip):
            self.log_suspicious_activity(
                request,
                f"Intento de acceso desde IP bloqueada: {client_ip}",
                "BLOCKED_IP_ACCESS"
            )
            return HttpResponseForbidden(
                "IP bloqueada por actividad sospechosa",
                content_type="text/plain"
            )
        
        # Rate limiting básico
        if self.is_rate_limited(client_ip):
            self.log_suspicious_activity(
                request,
                f"Rate limiting activado para IP: {client_ip}",
                "RATE_LIMITED"
            )
            return HttpResponse(
                "Demasiadas solicitudes. Intente más tarde.",
                status=429,
                content_type="text/plain"
            )
        
        return None
    
    def get_client_ip(self, request):
        """
        Obtiene la IP real del cliente
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_suspicious_path(self, path):
        """
        Verifica si la ruta es sospechosa
        """
        return any(suspicious_path in path for suspicious_path in self.SUSPICIOUS_PATHS)
    
    def is_suspicious_user_agent(self, user_agent):
        """
        Verifica si el user agent es sospechoso
        """
        return any(suspicious_ua in user_agent for suspicious_ua in self.SUSPICIOUS_USER_AGENTS)
    
    def is_ip_blocked(self, ip):
        """
        Verifica si la IP está bloqueada
        """
        return cache.get(f"blocked_ip_{ip}") is not None
    
    def block_ip_temporarily(self, ip, seconds):
        """
        Bloquea una IP temporalmente
        """
        cache.set(f"blocked_ip_{ip}", True, timeout=seconds)
        logger.warning(f"IP {ip} bloqueada por {seconds} segundos")
    
    def is_rate_limited(self, ip):
        """
        Implementa rate limiting básico
        """
        key = f"rate_limit_{ip}"
        requests = cache.get(key, 0)

        if requests >= 100:  # Máximo 100 requests por minuto
            return True

        cache.set(key, requests + 1, timeout=60)
        return False

    def is_ip_whitelisted(self, ip):
        """
        Verifica si la IP está en la lista blanca
        """
        return WhitelistedIP.objects.filter(ip=ip).exists()

    def log_suspicious_activity(self, request, message, activity_type):
        """
        Registra actividad sospechosa
        """
        client_ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        referer = request.META.get('HTTP_REFERER', 'Direct')
        
        log_message = (
            f"SECURITY_ALERT [{activity_type}] - "
            f"IP: {client_ip} - "
            f"Path: {request.path} - "
            f"Method: {request.method} - "
            f"User-Agent: {user_agent} - "
            f"Referer: {referer} - "
            f"Message: {message}"
        )
        
        # Log a archivo de seguridad
        security_logger = logging.getLogger('django.security')
        security_logger.warning(log_message)
        
        # Log a consola para monitoreo inmediato
        logger.warning(log_message)
