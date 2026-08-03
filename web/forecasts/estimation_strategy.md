# Estrategia de Estimación de Gastos Futuros - Propuesta

## Problema Actual
El sistema actual calcula un promedio general de los últimos 6 meses sin considerar:
- Diferencias por categoría (algunas son más predecibles que otras)
- Frecuencia de gastos (algunas categorías son mensuales, otras más espaciadas)
- Tendencia temporal (aumento o disminución)
- Variabilidad (algunas categorías son más estables)

## Propuesta de Mejora

### 1. **Sistema de Estimación por Categoría**

#### Categorías Recurrentes Identificadas:
- **Muy Recurrentes** (mensuales): Luz, Gas, Internet, Agua
- **Recurrentes Variables**: Supermercado, Combustible
- **Ocasionales**: Otras categorías

#### Estrategia:
1. **Calcular promedio por categoría** de los últimos 6 meses
2. **Aplicar promedio ponderado** (más peso a meses recientes)
3. **Considerar frecuencia** de gastos por categoría
4. **Ajustar por variabilidad** (usar mediana si hay mucha variación)

### 2. **Métodos de Cálculo Propuestos**

#### Método A: Promedio Ponderado por Categoría
```
Para cada categoría recurrente:
- Calcular promedio mensual de últimos 6 meses
- Aplicar pesos: [0.10, 0.10, 0.15, 0.15, 0.25, 0.25] (más peso a meses recientes)
- Sumar promedios de todas las categorías recurrentes
```

#### Método B: Promedio Simple por Categoría con Ajustes
```
Para cada categoría recurrente:
- Identificar frecuencia (mensual, bimestral, trimestral)
- Calcular promedio ajustado por frecuencia
- Usar mediana si hay mucha variación (outliers)
```

#### Método C: Híbrido (Recomendado)
```
1. Categorías muy recurrentes (Luz, Gas, Internet, Agua):
   - Promedio mensual de últimos 6 meses
   - Peso extra si hay al menos 1 gasto por mes

2. Categorías variables (Supermercado, Combustible):
   - Promedio ponderado (más peso a meses recientes)
   - Considerar tendencia (aumentando/disminuyendo)

3. Otras categorías:
   - Promedio general simple
```

### 3. **Implementación Técnica**

#### Nuevos Métodos Sugeridos:

1. `_calculate_category_based_estimate()`: Calcula estimación por categoría
2. `_identify_recurrent_categories()`: Identifica qué categorías son recurrentes
3. `_calculate_weighted_average()`: Calcula promedio ponderado
4. `_calculate_trend()`: Analiza tendencia (aumento/disminución)
5. `_get_category_frequency()`: Determina frecuencia de gastos por categoría

### 4. **Ventajas de la Nueva Estrategia**

✅ **Más Preciso**: Considera patrones específicos por categoría
✅ **Adaptativo**: Se ajusta automáticamente a cambios en hábitos
✅ **Transparente**: Muestra desglose por categoría
✅ **Robusto**: Maneja outliers y datos faltantes mejor

### 5. **Configuración Sugerida**

#### Categorías Recurrentes Configurables:
```python
RECURRENT_CATEGORIES = {
    'monthly': ['Luz', 'Gas', 'Internet', 'Agua'],
    'variable': ['Supermercado', 'Combustible'],
    'occasional': []  # Se calculan automáticamente
}
```

#### Pesos para Promedio Ponderado:
```python
TIME_WEIGHTS = [0.10, 0.10, 0.15, 0.15, 0.25, 0.25]  # Mes 6 a Mes 1
```

### 6. **Visualización Mejorada**

Mostrar en el dashboard:
- Desglose de estimación por categoría
- Indicador de confianza por categoría (basado en variabilidad)
- Tendencia (↑ aumento, ↓ disminución, → estable)

## Recomendación Final

**Implementar Método C (Híbrido)** con las siguientes características:

1. ✅ Cálculo por categoría para categorías recurrentes
2. ✅ Promedio ponderado para categorías variables
3. ✅ Detección automática de frecuencia
4. ✅ Fallback a promedio general si no hay suficientes datos
5. ✅ Visualización de confianza y tendencias

