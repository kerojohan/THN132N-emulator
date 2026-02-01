# Análisis de Tablas M y P - Oregon Scientific THN132N

## Resumen Ejecutivo

Se han recalculado las tablas M y P a partir de **2,174 tramas capturadas** que comienzan con el preámbulo conocido `555555559995a5a6aa6a`. Se descartaron 22 tramas que no tenían el preámbulo correcto.

## Hallazgos Principales

### 1. Las tablas M y P son específicas de cada sensor

El análisis reveló que existen **8 sensores diferentes** (identificados por house code) en las capturas, y cada uno tiene sus propias tablas M y P:

| House Code | Tramas | Precisión | Estado |
|------------|--------|-----------|--------|
| 3 | 468 | **94.44%** | ✅ Excelente |
| 96 | 174 | 80.46% | ✅ Bueno |
| 247 | 1,516 | 72.43% | ⚠️ Aceptable |
| 135 | 6 | 100.00% | ℹ️ Pocos datos |
| 0 | 4 | 100.00% | ℹ️ Pocos datos |
| 92 | 2 | 100.00% | ℹ️ Pocos datos |
| 251 | 2 | 100.00% | ℹ️ Pocos datos |
| 79 | 2 | 100.00% | ℹ️ Pocos datos |

### 2. Sensor Principal (House Code 3) - 94.44% de precisión

Este es el sensor con mejor precisión y datos suficientes para análisis:

#### Tabla P[d] - Décimas de temperatura
```python
P_TABLE = [
    0x075,  # P[0]
    0x000,  # P[1]
    0x09F,  # P[2]
    0x0EA,  # P[3]
    0x0C0,  # P[4]
    0x0B5,  # P[5]
    0x02A,  # P[6]
    0x05F,  # P[7]
    0x01E,  # P[8]
    0x06B,  # P[9]
]
```

#### Tabla M[e] - Temperaturas enteras (13°C a 40°C)
```python
M_TABLE = {
    13: 0x243,
    14: 0x2F5,
    15: 0x0C9,
    16: 0x03A,
    17: 0x06B,
    18: 0x1E1,
    19: 0x1B0,
    20: 0x162,
    21: 0x133,
    22: 0x1C0,
    23: 0x191,
    24: 0x127,
    25: 0x176,
    26: 0x185,
    27: 0x1D4,
    28: 0x1E8,
    29: 0x1B9,
    30: 0x165,
    31: 0x134,
    32: 0x1C7,
    33: 0x196,
    34: 0x120,
    40: 0x110,
}
```

### 3. Sensor Secundario (House Code 247) - 72.43% de precisión

Este sensor tiene más datos (1,516 tramas) pero menor precisión:

#### Tabla P[d]
```python
P_TABLE = [
    0x000,  # P[0]
    0x075,  # P[1]
    0x0EA,  # P[2]
    0x09F,  # P[3]
    0x0B5,  # P[4]
    0x0C0,  # P[5]
    0x05F,  # P[6]
    0x02A,  # P[7]
    0x06B,  # P[8]
    0x01E,  # P[9]
]
```

**Nota:** Esta tabla P es muy similar a la del sensor 3, pero con P[0] y P[1] intercambiados.

### 4. Sensor Terciario (House Code 96) - 80.46% de precisión

Este sensor muestra un patrón diferente en la tabla P:

#### Tabla P[d]
```python
P_TABLE = [
    0x01E,  # P[0]
    0x01E,  # P[1]  - Duplicado
    0x0F4,  # P[2]
    0x081,  # P[3]
    0x0DE,  # P[4]
    0x0DE,  # P[5]  - Duplicado
    0x034,  # P[6]
    0x034,  # P[7]  - Duplicado
    0x000,  # P[8]
    0x000,  # P[9]  - Duplicado
]
```

**Observación:** Este sensor tiene valores duplicados en P[d], lo que sugiere un patrón diferente de codificación.

## Fórmula de Cálculo

Para calcular el valor R12 a partir de una temperatura T en °C:

1. **Descomponer la temperatura:**
   - `e = int(T)` (parte entera)
   - `d = int(abs(T * 10)) % 10` (décima)

2. **Calcular R12:**
   - `R12 = M[e] ^ P[d]` (XOR)

3. **Codificar en el mensaje EC40:**
   - `msg[3] = (msg[3] & 0xF0) | ((R12 >> 8) & 0x0F)`
   - `msg[7] = R12 & 0xFF`

## Comparación con Tabla P Original

La tabla P original documentada era:
```python
P_ORIGINAL = [
    0x000,  # P[0]
    0x075,  # P[1]
    0x0EA,  # P[2]
    0x09F,  # P[3]
    0x0B5,  # P[4]
    0x0C0,  # P[5]
    0x05F,  # P[6]
    0x02A,  # P[7]
    0x06B,  # P[8]
    0x01E,  # P[9]
]
```

**Coincide exactamente con el sensor House 247**, pero difiere del sensor House 3 (el de mejor precisión) en P[0] y P[1].

## Conclusiones

1. **Las tablas M y P son específicas de cada sensor individual**, no universales para todos los THN132N.

2. **El sensor House Code 3 es el más confiable** con 94.44% de precisión y suficientes datos (468 tramas).

3. **La tabla P tiene ligeras variaciones entre sensores**, principalmente en P[0] y P[1].

4. **La tabla M es completamente diferente para cada sensor**, lo que confirma que cada sensor tiene su propio "secreto" de codificación.

5. **El preámbulo `555555559995a5a6aa6a` es consistente** en todas las tramas válidas.

## Recomendaciones

1. **Para implementación práctica:** Usar las tablas del sensor House Code 3 como referencia principal.

2. **Para máxima compatibilidad:** Implementar un sistema que pueda aprender las tablas M y P de cada sensor específico.

3. **Para debugging:** Verificar siempre el house code al analizar tramas.

4. **Para futuras capturas:** Separar las capturas por sensor desde el principio.

## Archivos Generados

- `recalc_M_P_tables.py` - Script para recalcular tablas (todas las tramas juntas)
- `recalc_M_P_per_sensor.py` - Script para recalcular tablas por sensor
- `tablas_M_P_recalculadas.md` - Documentación de tablas combinadas
- `tablas_M_P_por_sensor.md` - Documentación detallada por sensor
- `RESUMEN_TABLAS_M_P.md` - Este documento

## Próximos Pasos Sugeridos

1. Validar las tablas generadas transmitiendo con un ESP32/ATtiny85 y verificando la recepción.

2. Probar específicamente las temperaturas que mostraron errores en la verificación.

3. Capturar más datos del sensor House 3 para ampliar el rango de temperaturas en la tabla M.

4. Investigar por qué el sensor House 247 tiene menor precisión a pesar de tener más datos.
