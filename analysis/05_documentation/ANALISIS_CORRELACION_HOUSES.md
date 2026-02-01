# Análisis de Correlación entre House IDs en THN132N

## Resumen Ejecutivo

Se han analizado **106 tramas** capturadas con **6 house IDs diferentes**: 73, 132, 151, 155, 173 y 255.

## Hallazgos Principales

### 1. Relación Byte3 ↔ House Code

**CONFIRMADO:** El nibble alto de byte3 corresponde exactamente al nibble alto del house code.

```
House  73 (0x49) → b3_high = 0x4  ✓
House 132 (0x84) → b3_high = 0x8  ✓
House 151 (0x97) → b3_high = 0x9  ✓
House 155 (0x9B) → b3_high = 0x9  ✓
House 173 (0xAD) → b3_high = 0xA  ✓
House 255 (0xFF) → b3_high = 0xF  ✓
```

**Implicación:** El byte3 tiene la estructura:
- **Nibble alto:** Nibble alto del house code
- **Nibble bajo:** Parte alta de R12

### 2. ¿Son las Tablas M y P Universales?

**RESPUESTA: NO**

La hipótesis de que R12 es universal (independiente del house code) fue probada combinando todos los datos de todos los houses para calcular tablas M y P "universales". Los resultados:

- **Precisión global:** 34.91% (37/106 tramas)
- **Precisión por house:**
  - House 132: 64.29% ⭐ (mejor ajuste)
  - House 255: 46.88%
  - House 155: 35.29%
  - House 73: 30.77%
  - House 173: 14.29%
  - House 151: 0.00% (peor ajuste)

**Conclusión:** Las tablas M y P **SÍ dependen del house code**. No son universales.

### 3. Caso Especial: Temperatura 21.7°C

**IMPORTANTE:** Para 21.7°C, houses 151 (0x97) y 255 (0xFF) tienen **exactamente el mismo R12 = 0x87A**:

```
House 151 (0x97): R12=0x87A, b3_high=0x9, b7=0x7A
House 255 (0xFF): R12=0x87A, b3_high=0xF, b7=0x7A
```

Esto sugiere que aunque las tablas varían por house, pueden **coincidir ocasionalmente** en ciertos puntos.

### 4. Patrones XOR entre Tablas P

Al comparar las tablas P entre diferentes houses, se encontraron algunos patrones XOR:

**XOR casi constante:**
- House 73 vs 151: XOR constante = 0x0FA
- House 73 vs 132: 2 valores (0x0F4, 0x075)
- House 151 vs 173: 3 valores (0x0FA, 0x0B5, 0x05F)

**Sin patrón claro:** La mayoría de comparaciones entre houses no muestran un patrón XOR simple.

### 5. Cobertura de Datos

**Problema identificado:** Solo hay **2 temperaturas comunes** (20°C y 21°C) entre TODOS los house IDs.

Rangos de temperatura por house:
```
House  73: 20.1°C - 22.2°C (13 muestras)
House 132: 20.3°C - 21.8°C (14 muestras)
House 151: 20.4°C - 21.7°C (9 muestras)
House 155: 20.1°C - 22.7°C (17 muestras)
House 173: 18.4°C - 21.0°C (21 muestras)
House 255: 18.4°C - 23.0°C (32 muestras) ⭐ mejor cobertura
```

## Análisis de Tablas Individuales por House

Cuando se calculan tablas M y P de forma independiente para cada house:

- **Convergencia:** Todas convergen en 2-4 iteraciones
- **Precisión individual:** Entre 52% y 81%
  - House 173: 80.95% (mejor)
  - House 151: 77.78%
  - House 132: 64.29%
  - House 73: 61.54%
  - House 155: 52.94%
  - House 255: 53.12%

**Nota:** Las bajas precisiones indican que **necesitamos más datos** para cada house ID.

## Conclusiones

### ¿Qué sabemos con certeza?

1. ✅ **b3_high = (house_code >> 4) & 0x0F**
2. ✅ **R12 = ((byte3 & 0x0F) << 8) | byte7**
3. ✅ **Las tablas M y P NO son universales** - dependen del house code
4. ✅ **R12 = M[e] XOR P[d]** sigue siendo válido, pero M y P varían por house

### ¿Qué NO sabemos todavía?

1. ❓ **¿Cómo se derivan M y P del house code?**
   - No hay un patrón XOR simple y constante
   - Podría ser una función más compleja
   - Podría haber múltiples tablas dependiendo del nibble bajo del house

2. ❓ **¿Son las tablas específicas de cada sensor físico o derivables?**
   - Necesitamos capturar el mismo sensor con diferentes house codes configurados
   - O capturar múltiples sensores con el MISMO house code

3. ❓ **¿Por qué houses 151 y 255 tienen el mismo R12 en 21.7°C?**
   - ¿Coincidencia?
   - ¿Patrón oculto?

## Recomendaciones para Continuar

### Opción A: Más capturas con configuraciones controladas
1. Cambiar el house code del sensor manteniendo el hardware
2. Capturar temperaturas idénticas con diferentes houses
3. Esto revelaría si las tablas son derivables del house code

### Opción B: Aceptar que las tablas son específicas por sensor
1. Cada sensor tiene sus propias tablas M y P
2. El house code podría afectar las tablas, pero no de forma simple
3. Usar un proceso de calibración/captura para cada sensor

### Opción C: Análisis más profundo de los datos existentes
1. Buscar sub-patrones por nibble bajo del house
2. Intentar otras transformaciones (rotaciones, multiplicaciones)
3. Analizar si hay familias de houses con tablas similares

## Archivos Generados

- `analyze_multi_house.py`: Calcula tablas M y P individuales por house
- `analyze_byte3_house.py`: Analiza relación byte3 ↔ house code
- `test_universal_tables.py`: Prueba hipótesis de tablas universales
- `tablas_universales_live.txt`: Resultados de tablas combinadas (34.91% precisión)
