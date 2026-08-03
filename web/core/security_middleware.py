import ipaddress
import logging
import re

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

# Cuánto tiempo se cachea la lista blanca antes de volver a consultar la base.
WHITELIST_CACHE_SECONDS = 300


class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware de seguridad para detectar y bloquear intentos de ataque.

    Reglas de convivencia importantes:
      - Nunca bloquea IPs privadas (n8n, nginx proxy manager, la propia red
        de Docker). El bot de Telegram no se puede quedar afuera.
      - Sólo confía en X-Forwarded-For si la conexión viene de un proxy
        conocido; si no, cualquiera podría falsificar su IP.
    """

    # Rutas que sólo tiene sentido pedir si estás buscando un agujero.
    # OJO: acá NO van /robots.txt, /favicon.ico ni /.well-known/ (esta última
    # es la que usa Let's Encrypt para renovar el certificado).
    SUSPICIOUS_PATHS = [
        '/wordpress/',
        '/wp-admin/',
        '/wp-login.php',
        '/wp-content/',
        '/wp-includes/',
        '/administrator/',
        '/admin.php',
        '/phpmyadmin/',
        '/pma/',
        '/.env',
        '/config.php',
        '/xmlrpc.php',
        '/.git/',
        '/.svn/',
        '/backup/',
        '/shell.php',
        '/vendor/phpunit/',
        '/cgi-bin/',
        '/solr/',
        '/actuator/',
    ]

    # User agents de herramientas de escaneo. Se comparan como palabra
    # completa para no bloquear, por ejemplo, a Googlebot por contener "bot".
    SUSPICIOUS_USER_AGENTS = [
        'sqlmap',
        'nikto',
        'nmap',
        'masscan',
        'zgrab',
        'nuclei',
        'dirbuster',
        'gobuster',
        'wpscan',
        'acunetix',
        'burpsuite',
        'zaproxy',
    ]

    _UA_REGEX = re.compile(
        r'(?:^|[^a-z0-9])(' + '|'.join(SUSPICIOUS_USER_AGENTS) + r')(?:[^a-z0-9]|$)'
    )

    # Prefijos que nunca se analizan (estáticos y archivos que pide el navegador).
    EXEMPT_PREFIXES = ('/static/', '/media/', '/.well-known/')
    EXEMPT_PATHS = ('/robots.txt', '/favicon.ico', '/sitemap.xml')

    def process_request(self, request):
        path = request.path.lower()

        # Rutas exentas: ni se miran.
        if path in self.EXEMPT_PATHS or path.startswith(self.EXEMPT_PREFIXES):
            return None

        client_ip = self.get_client_ip(request)

        # Tráfico interno (n8n, nginx, otros contenedores): nunca se bloquea.
        if self.is_internal_ip(client_ip):
            return None

        # Lista blanca configurada por el usuario.
        if self.is_ip_whitelisted(client_ip):
            return None

        # Si ya está bloqueada, cortar antes que nada.
        if self.is_ip_blocked(client_ip):
            return HttpResponseForbidden(
                "IP bloqueada por actividad sospechosa",
                content_type="text/plain",
            )

        if self.is_suspicious_path(path):
            self.log_suspicious_activity(
                request,
                f"Intento de acceso a ruta sospechosa: {path}",
                "SUSPICIOUS_PATH",
            )
            self.block_ip_temporarily(client_ip, 3600, f'Ruta sospechosa: {path}')  # 1 hora
            return HttpResponseForbidden(
                "Acceso denegado por razones de seguridad",
                content_type="text/plain",
            )

        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        if self.is_suspicious_user_agent(user_agent):
            self.log_suspicious_activity(
                request,
                f"User agent sospechoso: {user_agent}",
                "SUSPICIOUS_USER_AGENT",
            )
            self.block_ip_temporarily(client_ip, 1800, 'User agent de escaneo')  # 30 minutos
            return HttpResponseForbidden(
                "Acceso denegado por razones de seguridad",
                content_type="text/plain",
            )

        if self.is_rate_limited(client_ip):
            self.log_suspicious_activity(
                request,
                f"Rate limiting activado para IP: {client_ip}",
                "RATE_LIMITED",
            )
            return HttpResponse(
                "Demasiadas solicitudes. Intente más tarde.",
                status=429,
                content_type="text/plain",
            )

        return None

    # ------------------------------------------------------------------
    # Identificación del cliente
    # ------------------------------------------------------------------

    def get_client_ip(self, request):
        """
        Devuelve la IP real del cliente.

        X-Forwarded-For lo puede escribir cualquiera, así que sólo se le hace
        caso cuando la conexión llega desde un proxy de confianza (nginx proxy
        manager, que corre en la red privada de Docker).
        """
        remote_addr = request.META.get('REMOTE_ADDR', '')

        if self.is_trusted_proxy(remote_addr):
            forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
            if forwarded:
                # El primer valor es el cliente original.
                candidate = forwarded.split(',')[0].strip()
                if self._parse_ip(candidate):
                    return candidate

        return remote_addr

    def is_trusted_proxy(self, ip):
        """Un proxy es de confianza si está listado, o si es una IP privada."""
        if ip in getattr(settings, 'TRUSTED_PROXY_IPS', []):
            return True
        return self.is_internal_ip(ip)

    def is_internal_ip(self, ip):
        """True para loopback y redes privadas (la red interna de Docker)."""
        parsed = self._parse_ip(ip)
        if parsed is None:
            return False
        return parsed.is_private or parsed.is_loopback

    @staticmethod
    def _parse_ip(value):
        try:
            return ipaddress.ip_address(value)
        except ValueError:
            return None

    # ------------------------------------------------------------------
    # Detecciones
    # ------------------------------------------------------------------

    def is_suspicious_path(self, path):
        return any(p in path for p in self.SUSPICIOUS_PATHS)

    def is_suspicious_user_agent(self, user_agent):
        if not user_agent:
            return False
        return bool(self._UA_REGEX.search(user_agent))

    def is_ip_blocked(self, ip):
        return cache.get(f"blocked_ip_{ip}") is not None

    def block_ip_temporarily(self, ip, seconds, reason='Actividad sospechosa'):
        cache.set(f"blocked_ip_{ip}", True, timeout=seconds)
        logger.warning(f"IP {ip} bloqueada por {seconds} segundos")

        # Además se deja registro en la base para que aparezca en la pantalla
        # de "IPs bloqueadas" y se pueda desbloquear desde ahí.
        try:
            from security.models import BlockedIP
            BlockedIP.objects.get_or_create(
                ip=ip[:15],
                defaults={'reason': f'{reason} (bloqueo automático de {seconds // 60} min)'},
            )
        except Exception as exc:
            logger.warning(f"No se pudo registrar la IP bloqueada {ip}: {exc}")

    def is_rate_limited(self, ip):
        """
        Ventana fija de 60 segundos. Se usa incr para no reiniciar el TTL en
        cada request (si no, la ventana no cerraba nunca bajo tráfico continuo).
        """
        key = f"rate_limit_{ip}"
        try:
            count = cache.incr(key)
        except ValueError:
            # La clave no existía: se crea con TTL de 60s.
            cache.set(key, 1, timeout=60)
            return False

        return count > 100  # máximo 100 requests por minuto

    def is_ip_whitelisted(self, ip):
        """Consulta la lista blanca usando caché para no pegarle a la BD en cada request."""
        cache_key = 'security_whitelisted_ips'
        whitelisted = cache.get(cache_key)

        if whitelisted is None:
            try:
                from security.models import WhitelistedIP
                whitelisted = set(
                    WhitelistedIP.objects.values_list('ip', flat=True)
                )
            except Exception as exc:  # la tabla puede no existir todavía (migraciones)
                logger.warning(f"No se pudo leer la lista blanca: {exc}")
                return False
            cache.set(cache_key, whitelisted, timeout=WHITELIST_CACHE_SECONDS)

        return ip in whitelisted

    # ------------------------------------------------------------------

    def log_suspicious_activity(self, request, message, activity_type):
        client_ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        referer = request.META.get('HTTP_REFERER', 'Direct')

        logger.warning(
            f"SECURITY_ALERT [{activity_type}] - "
            f"IP: {client_ip} - "
            f"Path: {request.path} - "
            f"Method: {request.method} - "
            f"User-Agent: {user_agent} - "
            f"Referer: {referer} - "
            f"Message: {message}"
        )
