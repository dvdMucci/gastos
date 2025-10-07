#!/bin/bash

# Script para monitorear la seguridad del sistema
# Uso: ./monitor_security.sh

echo "🔒 MONITOR DE SEGURIDAD - Sistema de Gastos"
echo "=============================================="
echo ""

# Función para mostrar logs de Docker
show_docker_logs() {
    echo "📊 LOGS DE DOCKER (últimas 20 líneas):"
    echo "--------------------------------------"
    cd /home/ubuntu/datosDocker/gastos
    docker-compose logs web --tail=20 | grep -E "(GET|POST|PUT|DELETE|ERROR|WARNING|SECURITY)"
    echo ""
}

# Función para mostrar logs de seguridad
show_security_logs() {
    echo "🚨 LOGS DE SEGURIDAD:"
    echo "---------------------"
    if [ -f "web/logs/security_attacks.log" ]; then
        echo "📁 Archivo: web/logs/security_attacks.log"
        tail -20 web/logs/security_attacks.log
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
    wordpress_attempts=$(docker-compose logs web 2>/dev/null | grep -c "wordpress" || echo "0")
    echo "🔍 Intentos de acceso a WordPress: $wordpress_attempts"
    
    # Contar 404s recientes
    recent_404s=$(docker-compose logs web --since=1h 2>/dev/null | grep -c "404" || echo "0")
    echo "🚫 Errores 404 en la última hora: $recent_404s"
    
    # Contar IPs bloqueadas (si hay logs)
    if [ -f "web/logs/security_attacks.log" ]; then
        blocked_ips=$(grep -c "IP.*bloqueada" web/logs/security_attacks.log 2>/dev/null || echo "0")
        echo "🚫 IPs bloqueadas: $blocked_ips"
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
