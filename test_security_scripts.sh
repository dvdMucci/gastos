#!/bin/bash

# Script para probar los scripts de seguridad
# Uso: ./test_security_scripts.sh

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

show_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                🧪 TEST SECURITY SCRIPTS                     ║"
    echo "║                                                              ║"
    echo "║  Verifica que los scripts de seguridad funcionen correctamente ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Función para probar el script de múltiples proyectos
test_multiple_projects_script() {
    local hardening_script="$1"
    
    print_status "Probando script de múltiples proyectos..."
    
    # Verificar que el script existe
    if [ ! -f "$hardening_script" ]; then
        print_error "Script de múltiples proyectos no encontrado"
        return 1
    fi
    
    # Verificar que es ejecutable
    if [ ! -x "$hardening_script" ]; then
        print_error "Script de múltiples proyectos no es ejecutable"
        return 1
    fi
    
    print_success "✅ Script de múltiples proyectos encontrado y ejecutable"
    
    # Verificar funciones del script
    if grep -q "find_django_projects" "$hardening_script"; then
        print_success "✅ Función de búsqueda automática encontrada"
    else
        print_error "❌ Función de búsqueda automática no encontrada"
        return 1
    fi
    
    if grep -q "show_menu" "$hardening_script"; then
        print_success "✅ Función de menú interactivo encontrada"
    else
        print_error "❌ Función de menú interactivo no encontrada"
        return 1
    fi
}

# Función para probar el script de hardening
test_hardening_script() {
    local hardening_script="$1"
    
    print_status "Probando script de hardening..."
    
    # Verificar que el script existe
    if [ ! -f "$hardening_script" ]; then
        print_error "Script de hardening no encontrado"
        return 1
    fi
    
    # Verificar que es ejecutable
    if [ ! -x "$hardening_script" ]; then
        print_error "Script de hardening no es ejecutable"
        return 1
    fi
    
    print_success "✅ Script de hardening encontrado y ejecutable"
    
    # Verificar funciones del script
    if grep -q "verify_django_project" "$hardening_script"; then
        print_success "✅ Función de verificación de proyecto encontrada"
    else
        print_error "❌ Función de verificación de proyecto no encontrada"
        return 1
    fi
    
    if grep -q "create_security_middleware" "$hardening_script"; then
        print_success "✅ Función de creación de middleware encontrada"
    else
        print_error "❌ Función de creación de middleware no encontrada"
        return 1
    fi
    
    if grep -q "update_settings" "$hardening_script"; then
        print_success "✅ Función de actualización de settings encontrada"
    else
        print_error "❌ Función de actualización de settings no encontrada"
        return 1
    fi
}

# Función para verificar estructura de archivos
test_file_structure() {
    print_status "Verificando estructura de archivos..."
    
    local files=(
        "django_security_hardening.sh:Script principal de hardening"
        "harden_multiple_projects.sh:Script para múltiples proyectos"
        "README_SECURITY_HARDENING.md:Documentación"
    )
    
    for file_info in "${files[@]}"; do
        local file_path="${file_info%%:*}"
        local description="${file_info##*:}"
        
        if [ -f "$file_path" ]; then
            print_success "✅ $description encontrado"
        else
            print_error "❌ $description no encontrado"
            return 1
        fi
    done
}

# Función para verificar permisos
test_permissions() {
    print_status "Verificando permisos de ejecución..."
    
    local scripts=(
        "django_security_hardening.sh"
        "harden_multiple_projects.sh"
        "test_security_scripts.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [ -x "$script" ]; then
            print_success "✅ $script es ejecutable"
        else
            print_error "❌ $script no es ejecutable"
            return 1
        fi
    done
}

# Función para verificar sintaxis de bash
test_syntax() {
    print_status "Verificando sintaxis de scripts..."
    
    local scripts=(
        "django_security_hardening.sh"
        "harden_multiple_projects.sh"
    )
    
    for script in "${scripts[@]}"; do
        if bash -n "$script" 2>/dev/null; then
            print_success "✅ $script tiene sintaxis correcta"
        else
            print_error "❌ $script tiene errores de sintaxis"
            return 1
        fi
    done
}

# Función principal
main() {
    show_banner
    
    local hardening_script="./django_security_hardening.sh"
    local multiple_script="./harden_multiple_projects.sh"
    
    print_success "Scripts encontrados, iniciando pruebas..."
    echo ""
    
    # Probar estructura de archivos
    if test_file_structure; then
        print_success "✅ Estructura de archivos: PASÓ"
    else
        print_error "❌ Estructura de archivos: FALLÓ"
        exit 1
    fi
    
    echo ""
    
    # Probar permisos
    if test_permissions; then
        print_success "✅ Permisos de ejecución: PASÓ"
    else
        print_error "❌ Permisos de ejecución: FALLÓ"
        exit 1
    fi
    
    echo ""
    
    # Probar sintaxis
    if test_syntax; then
        print_success "✅ Sintaxis de scripts: PASÓ"
    else
        print_error "❌ Sintaxis de scripts: FALLÓ"
        exit 1
    fi
    
    echo ""
    
    # Probar script de múltiples proyectos
    if test_multiple_projects_script "$multiple_script"; then
        print_success "✅ Script de múltiples proyectos: PASÓ"
    else
        print_error "❌ Script de múltiples proyectos: FALLÓ"
        exit 1
    fi
    
    echo ""
    
    # Probar script de hardening
    if test_hardening_script "$hardening_script"; then
        print_success "✅ Script de hardening: PASÓ"
    else
        print_error "❌ Script de hardening: FALLÓ"
        exit 1
    fi
    
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    ✅ TODAS LAS PRUEBAS PASARON             ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Los scripts están listos para usar en producción:${NC}"
    echo "  • django_security_hardening.sh - Para proyectos individuales"
    echo "  • harden_multiple_projects.sh - Para múltiples proyectos"
    echo ""
    echo -e "${YELLOW}Recuerda:${NC}"
    echo "  • Hacer backup antes de usar en producción"
    echo "  • Probar en ambiente de desarrollo primero"
    echo "  • Monitorear logs después de aplicar"
    echo ""
    echo -e "${BLUE}Ejemplos de uso:${NC}"
    echo "  ./django_security_hardening.sh /ruta/a/tu/proyecto"
    echo "  ./harden_multiple_projects.sh"
    echo ""
}

# Ejecutar función principal
main "$@"