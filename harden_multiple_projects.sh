#!/bin/bash

# Script para aplicar hardening de seguridad a múltiples proyectos Django
# Uso: ./harden_multiple_projects.sh

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

show_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║           🛡️  MULTIPLE DJANGO PROJECTS HARDENING           ║"
    echo "║                                                              ║"
    echo "║  Aplica medidas de seguridad a múltiples proyectos Django    ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Verificar que el script de hardening existe
if [ ! -f "./django_security_hardening.sh" ]; then
    print_error "No se encontró django_security_hardening.sh"
    print_error "Asegúrate de que esté en el mismo directorio"
    exit 1
fi

show_banner

echo "Este script te ayudará a aplicar hardening de seguridad a múltiples proyectos Django."
echo ""

# Función para buscar proyectos Django automáticamente
find_django_projects() {
    print_status "Buscando proyectos Django en el sistema..."
    
    # Buscar proyectos Django comunes
    local projects=()
    
    # Buscar en directorios comunes
    local search_paths=(
        "/home/$USER/proyectos"
        "/home/$USER/django"
        "/home/$USER/websites"
        "/home/$USER/apps"
        "/home/$USER/datosDocker/lcc-ot"
        "/home/$USER/datosDocker/lcc-pg"
        "/root/datosDocker/lcc-ot"
        "/root/datosDocker/lcc-pg"
        "/var/www"
        "/opt"
        "$HOME"
    )
    
    for path in "${search_paths[@]}"; do
        if [ -d "$path" ]; then
            # Buscar proyectos Django (que tengan manage.py)
            while IFS= read -r -d '' project; do
                if [ -f "$project/manage.py" ]; then
                    projects+=("$project")
                fi
            done < <(find "$path" -maxdepth 3 -name "manage.py" -type f -print0 2>/dev/null)
        fi
    done
    
    echo "${projects[@]}"
}

# Función para mostrar menú interactivo
show_menu() {
    echo "Opciones disponibles:"
    echo ""
    echo "1. Buscar proyectos Django automáticamente"
    echo "2. Ingresar rutas manualmente"
    echo "3. Salir"
    echo ""
    read -p "Selecciona una opción (1-3): " choice
    
    case $choice in
        1)
            auto_find_projects
            ;;
        2)
            manual_input_projects
            ;;
        3)
            print_status "Saliendo..."
            exit 0
            ;;
        *)
            print_error "Opción inválida"
            show_menu
            ;;
    esac
}

# Función para búsqueda automática
auto_find_projects() {
    print_status "Buscando proyectos Django..."
    
    local projects=($(find_django_projects))
    
    if [ ${#projects[@]} -eq 0 ]; then
        print_warning "No se encontraron proyectos Django automáticamente"
        manual_input_projects
        return
    fi
    
    echo ""
    print_success "Proyectos Django encontrados:"
    echo ""
    
    for i in "${!projects[@]}"; do
        echo "$((i+1)). ${projects[$i]}"
    done
    
    echo ""
    read -p "¿Deseas aplicar hardening a todos estos proyectos? (y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        apply_hardening_to_projects "${projects[@]}"
    else
        select_specific_projects "${projects[@]}"
    fi
}

# Función para seleccionar proyectos específicos
select_specific_projects() {
    local projects=("$@")
    
    echo ""
    echo "Selecciona los proyectos a proteger (separados por comas, ej: 1,3,5):"
    read -p "Proyectos: " selection
    
    local selected_projects=()
    IFS=',' read -ra indices <<< "$selection"
    
    for index in "${indices[@]}"; do
        index=$((index-1))  # Convertir a índice basado en 0
        if [ $index -ge 0 ] && [ $index -lt ${#projects[@]} ]; then
            selected_projects+=("${projects[$index]}")
        else
            print_warning "Índice inválido: $((index+1))"
        fi
    done
    
    if [ ${#selected_projects[@]} -gt 0 ]; then
        apply_hardening_to_projects "${selected_projects[@]}"
    else
        print_error "No se seleccionaron proyectos válidos"
    fi
}

# Función para entrada manual
manual_input_projects() {
    echo ""
    echo "Ingresa las rutas de tus proyectos Django (una por línea):"
    echo "Presiona Enter en una línea vacía cuando termines"
    echo ""
    
    local projects=()
    local project_path
    
    while true; do
        read -p "Ruta del proyecto: " project_path
        if [ -z "$project_path" ]; then
            break
        fi
        
        if [ -d "$project_path" ] && [ -f "$project_path/manage.py" ]; then
            projects+=("$project_path")
            print_success "Proyecto válido agregado: $project_path"
        else
            print_warning "Proyecto inválido o no encontrado: $project_path"
        fi
    done
    
    if [ ${#projects[@]} -gt 0 ]; then
        apply_hardening_to_projects "${projects[@]}"
    else
        print_error "No se ingresaron proyectos válidos"
    fi
}

# Función para aplicar hardening a múltiples proyectos
apply_hardening_to_projects() {
    local projects=("$@")
    local total_projects=${#projects[@]}
    local success_count=0
    local failed_count=0
    
    echo ""
    print_status "Aplicando hardening de seguridad a $total_projects proyectos..."
    echo ""
    
    for i in "${!projects[@]}"; do
        local project="${projects[$i]}"
        local project_name=$(basename "$project")
        
        echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║ Proyecto $((i+1))/$total_projects: $project_name${NC}"
        echo -e "${BLUE}║ Ruta: $project${NC}"
        echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        
        # Ejecutar el script de hardening
        if ./django_security_hardening.sh "$project"; then
            print_success "✅ Hardening completado para: $project_name"
            ((success_count++))
        else
            print_error "❌ Error en hardening para: $project_name"
            ((failed_count++))
        fi
        
        echo ""
        echo "----------------------------------------"
        echo ""
    done
    
    # Mostrar resumen final
    show_final_summary "$total_projects" "$success_count" "$failed_count"
}

# Función para mostrar resumen final
show_final_summary() {
    local total="$1"
    local success="$2"
    local failed="$3"
    
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    📊 RESUMEN FINAL                          ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Total de proyectos procesados:${NC} $total"
    echo -e "${GREEN}Proyectos protegidos exitosamente:${NC} $success"
    echo -e "${RED}Proyectos con errores:${NC} $failed"
    echo ""
    
    if [ "$success" -gt 0 ]; then
        echo -e "${GREEN}✅ Proyectos protegidos:${NC}"
        echo "  • Middleware de seguridad activo"
        echo "  • DEBUG deshabilitado en producción"
        echo "  • Headers de seguridad configurados"
        echo "  • Rate limiting implementado"
        echo "  • Logging de seguridad activo"
        echo "  • Bloqueo automático de IPs maliciosas"
        echo ""
    fi
    
    if [ "$failed" -gt 0 ]; then
        echo -e "${RED}❌ Proyectos con errores requieren revisión manual${NC}"
        echo ""
    fi
    
    echo -e "${YELLOW}📋 Próximos pasos recomendados:${NC}"
    echo "  1. Reiniciar todos los servidores Django protegidos"
    echo "  2. Ejecutar monitor_security.sh en cada proyecto"
    echo "  3. Monitorear logs/security_attacks.log"
    echo "  4. Revisar logs diariamente"
    echo "  5. Mantener dependencias actualizadas"
    echo ""
    echo -e "${BLUE}🕒 Proceso completado: $(date)${NC}"
    echo ""
}

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0"
    echo ""
    echo "Este script aplica medidas de seguridad a múltiples proyectos Django:"
    echo ""
    echo "Características:"
    echo "  • Búsqueda automática de proyectos Django"
    echo "  • Entrada manual de rutas de proyectos"
    echo "  • Hardening automático de todos los proyectos"
    echo "  • Resumen detallado del proceso"
    echo ""
    echo "Medidas de seguridad aplicadas:"
    echo "  • Middleware de seguridad personalizado"
    echo "  • DEBUG deshabilitado en producción"
    echo "  • Headers de seguridad (HSTS, XSS, etc.)"
    echo "  • Rate limiting y bloqueo de IPs"
    echo "  • Logging de seguridad detallado"
    echo "  • Detección de ataques automática"
    echo ""
}

# Verificar argumentos
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

# Ejecutar menú principal
show_menu
