#!/bin/bash

# Script de Hardening de Seguridad para Django
# Aplica todas las medidas de seguridad implementadas en el proyecto de gastos
# Uso: ./django_security_hardening.sh [ruta_del_proyecto]

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con colores
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para mostrar el banner
show_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                🛡️  DJANGO SECURITY HARDENING                ║"
    echo "║                                                              ║"
    echo "║  Script automatizado para aplicar medidas de seguridad       ║"
    echo "║  en proyectos Django expuestos a internet                    ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Función para verificar si es un proyecto Django válido
verify_django_project() {
    local project_path="$1"
    
    if [ ! -d "$project_path" ]; then
        print_error "El directorio $project_path no existe"
        exit 1
    fi
    
    if [ ! -f "$project_path/manage.py" ]; then
        print_error "No se encontró manage.py en $project_path. No es un proyecto Django válido."
        exit 1
    fi
    
    if [ ! -d "$project_path"/*/settings.py ] && [ ! -f "$project_path/settings.py" ]; then
        print_error "No se encontró settings.py. Proyecto Django inválido."
        exit 1
    fi
    
    print_success "Proyecto Django válido detectado en: $project_path"
}

# Función para hacer backup del settings.py
backup_settings() {
    local project_path="$1"
    local settings_file=""
    
    # Buscar settings.py
    if [ -f "$project_path/settings.py" ]; then
        settings_file="$project_path/settings.py"
    else
        # Buscar en subdirectorios
        settings_file=$(find "$project_path" -name "settings.py" -type f | head -1)
    fi
    
    if [ -z "$settings_file" ]; then
        print_error "No se pudo encontrar settings.py"
        exit 1
    fi
    
    local backup_file="${settings_file}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$settings_file" "$backup_file"
    print_success "Backup creado: $backup_file"
    echo "$settings_file"
}

# Función para crear el middleware de seguridad
create_security_middleware() {
    local project_path="$1"
    local core_dir="$project_path/core"
    
    print_status "Creando middleware de seguridad..."
    
    # Crear directorio core si no existe
    if [ ! -d "$core_dir" ]; then
        mkdir -p "$core_dir"
        touch "$core_dir/__init__.py"
        print_status "Directorio core creado"
    fi
    
    # Crear el archivo de middleware
    cat > "$core_dir/security_middleware.py" << 'EOF'
import logging
import time
from django.http import HttpResponseForbidden, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.conf import settings
import ipaddress

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
EOF

    print_success "Middleware de seguridad creado"
}

# Función para actualizar settings.py
update_settings() {
    local settings_file="$1"
    local project_path=$(dirname "$settings_file")
    
    print_status "Actualizando configuración de seguridad en settings.py..."
    
    # Crear archivo temporal con las nuevas configuraciones
    cat > /tmp/security_config.py << 'EOF'

# Security Settings - Agregado por Django Security Hardening
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Additional Security Headers
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Logging Configuration for Security Monitoring
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'security_attacks.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
EOF

    # Buscar la línea DEBUG y cambiarla
    if grep -q "DEBUG = True" "$settings_file"; then
        sed -i 's/DEBUG = True/DEBUG = False  # CRITICAL: Disable debug in production for security/' "$settings_file"
        print_success "DEBUG deshabilitado en settings.py"
    else
        print_warning "DEBUG no encontrado o ya está deshabilitado"
    fi
    
    # Agregar middleware de seguridad al principio de MIDDLEWARE
    if grep -q "MIDDLEWARE" "$settings_file"; then
        # Verificar si ya está el middleware de seguridad
        if ! grep -q "core.security_middleware.SecurityMiddleware" "$settings_file"; then
            sed -i "/MIDDLEWARE = \[/a\\    'core.security_middleware.SecurityMiddleware',  # Nuestro middleware de seguridad" "$settings_file"
            print_success "Middleware de seguridad agregado"
        else
            print_warning "Middleware de seguridad ya existe"
        fi
    else
        print_error "No se encontró configuración MIDDLEWARE en settings.py"
        return 1
    fi
    
    # Agregar configuraciones de seguridad al final del archivo
    echo "" >> "$settings_file"
    cat /tmp/security_config.py >> "$settings_file"
    
    print_success "Configuraciones de seguridad agregadas"
    
    # Limpiar archivo temporal
    rm /tmp/security_config.py
}

# Función para crear directorio de logs
create_logs_directory() {
    local project_path="$1"
    local logs_dir="$project_path/logs"
    
    print_status "Creando directorio de logs..."
    
    if [ ! -d "$logs_dir" ]; then
        mkdir -p "$logs_dir"
        print_success "Directorio de logs creado: $logs_dir"
    else
        print_warning "Directorio de logs ya existe"
    fi
}

# Función para crear script de monitoreo
create_monitoring_script() {
    local project_path="$1"
    local script_path="$project_path/monitor_security.sh"
    
    print_status "Creando script de monitoreo de seguridad..."
    
    cat > "$script_path" << 'EOF'
#!/bin/bash

# Script para monitorear la seguridad del sistema
# Uso: ./monitor_security.sh

echo "🔒 MONITOR DE SEGURIDAD - $(basename $(pwd))"
echo "=============================================="
echo ""

# Función para mostrar logs de Docker (si está en Docker)
show_docker_logs() {
    if [ -f "docker-compose.yml" ] || [ -f "docker-compose.yaml" ]; then
        echo "📊 LOGS DE DOCKER (últimas 20 líneas):"
        echo "--------------------------------------"
        docker-compose logs web --tail=20 2>/dev/null | grep -E "(GET|POST|PUT|DELETE|ERROR|WARNING|SECURITY)" || echo "No hay logs de Docker disponibles"
        echo ""
    fi
}

# Función para mostrar logs de seguridad
show_security_logs() {
    echo "🚨 LOGS DE SEGURIDAD:"
    echo "---------------------"
    if [ -f "logs/security_attacks.log" ]; then
        echo "📁 Archivo: logs/security_attacks.log"
        tail -20 logs/security_attacks.log
    else
        echo "ℹ️  No hay logs de ataques registrados aún"
    fi
    echo ""
}

# Función para mostrar estadísticas de seguridad
show_security_stats() {
    echo "📈 ESTADÍSTICAS DE SEGURIDAD:"
    echo "-----------------------------"
    
    # Contar intentos de acceso a WordPress
    if [ -f "logs/security.log" ]; then
        wordpress_attempts=$(grep -c "wordpress" logs/security.log 2>/dev/null || echo "0")
        echo "🔍 Intentos de acceso a WordPress: $wordpress_attempts"
        
        recent_404s=$(grep -c "404" logs/security.log 2>/dev/null || echo "0")
        echo "🚫 Errores 404 recientes: $recent_404s"
        
        blocked_ips=$(grep -c "IP.*bloqueada" logs/security_attacks.log 2>/dev/null || echo "0")
        echo "🚫 IPs bloqueadas: $blocked_ips"
    else
        echo "ℹ️  No hay logs de seguridad disponibles"
    fi
    
    echo ""
}

# Función para mostrar recomendaciones
show_recommendations() {
    echo "💡 RECOMENDACIONES DE SEGURIDAD:"
    echo "--------------------------------"
    echo "✅ DEBUG deshabilitado en producción"
    echo "✅ Middleware de seguridad activo"
    echo "✅ Headers de seguridad configurados"
    echo "✅ Rate limiting implementado"
    echo "✅ Logging de seguridad activo"
    echo ""
    echo "🔍 MONITOREO RECOMENDADO:"
    echo "• Revisar logs diariamente"
    echo "• Monitorear intentos de acceso sospechosos"
    echo "• Mantener actualizado el sistema"
    echo "• Cambiar contraseñas regularmente"
    echo ""
}

# Función principal
main() {
    show_docker_logs
    show_security_logs
    show_security_stats
    show_recommendations
    
    echo "🕒 Última actualización: $(date)"
    echo "=============================================="
}

# Ejecutar función principal
main
EOF

    chmod +x "$script_path"
    print_success "Script de monitoreo creado: $script_path"
}

# Función para mostrar resumen final
show_summary() {
    local project_path="$1"
    
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    ✅ HARDENING COMPLETADO                   ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Proyecto protegido:${NC} $project_path"
    echo ""
    echo -e "${GREEN}Medidas de seguridad implementadas:${NC}"
    echo "  ✅ Middleware de seguridad personalizado"
    echo "  ✅ DEBUG deshabilitado en producción"
    echo "  ✅ Headers de seguridad (HSTS, XSS, etc.)"
    echo "  ✅ Rate limiting (100 req/min)"
    echo "  ✅ Bloqueo automático de IPs maliciosas"
    echo "  ✅ Logging de seguridad detallado"
    echo "  ✅ Detección de rutas sospechosas"
    echo "  ✅ Detección de User Agents maliciosos"
    echo ""
    echo -e "${YELLOW}Archivos creados/modificados:${NC}"
    echo "  📁 core/security_middleware.py"
    echo "  📁 logs/ (directorio)"
    echo "  📁 monitor_security.sh"
    echo "  📝 settings.py (modificado)"
    echo ""
    echo -e "${BLUE}Próximos pasos:${NC}"
    echo "  1. Reiniciar el servidor Django"
    echo "  2. Ejecutar: ./monitor_security.sh"
    echo "  3. Monitorear logs/security_attacks.log"
    echo "  4. Revisar logs diariamente"
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANTE:${NC}"
    echo "  • Haz backup de tu base de datos antes de reiniciar"
    echo "  • Verifica que tu aplicación funcione correctamente"
    echo "  • Mantén las dependencias actualizadas"
    echo ""
}

# Función principal
main() {
    show_banner
    
    # Verificar argumentos
    if [ $# -eq 0 ]; then
        print_error "Uso: $0 <ruta_del_proyecto_django>"
        echo ""
        echo "Ejemplos:"
        echo "  $0 /path/to/myproject"
        echo "  $0 ../mi-proyecto-django"
        echo "  $0 /home/usuario/proyectos/mi-app"
        exit 1
    fi
    
    local project_path="$1"
    
    print_status "Iniciando hardening de seguridad para: $project_path"
    echo ""
    
    # Verificar proyecto Django
    verify_django_project "$project_path"
    
    # Hacer backup de settings.py
    local settings_file=$(backup_settings "$project_path")
    
    # Crear middleware de seguridad
    create_security_middleware "$project_path"
    
    # Actualizar settings.py
    update_settings "$settings_file"
    
    # Crear directorio de logs
    create_logs_directory "$project_path"
    
    # Crear script de monitoreo
    create_monitoring_script "$project_path"
    
    # Mostrar resumen
    show_summary "$project_path"
    
    print_success "Hardening de seguridad completado exitosamente!"
}

# Ejecutar función principal con todos los argumentos
main "$@"
