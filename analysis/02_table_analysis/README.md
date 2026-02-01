# 02 - Table Analysis / Análisis de Tablas

Scripts para calcular y analizar las tablas de codificación M y P del protocolo Oregon THN132N.

## Concepto

El sensor usa dos tablas para codificar la temperatura:
- **Tabla M**: Mapea temperatura entera → valor M
- **Tabla P**: Mapea temperatura décima (0-9) → valor P
- **R12**: Valor de 12 bits calculado como `R12 = M[e] XOR P[d]`

## Scripts Principales

### `calc_universal_tables.py`
Calcula tablas M y P combinando datos de todos los house codes.

**Uso:**
```bash
python3 calc_universal_tables.py ../ec40_capturas_merged.csv
```

**Output:** Tablas M y P universales con estadísticas de precisión

### `recalc_M_P_tables.py`
Recalcula tablas M y P con algoritmo iterativo mejorado.

**Uso:**
```bash
python3 recalc_M_P_tables.py ../ec40_capturas_merged.csv
```

### `recalc_M_P_per_sensor.py`
Calcula tablas independientes para cada sensor (por house code).

**Uso:**
```bash
python3 recalc_M_P_per_sensor.py ../ec40_capturas_merged.csv
```

## Scripts de Soporte

### `calc_M_desde_csv.py`
Calcula solo la tabla M desde capturas CSV.

### `analyze_p_derivation.py`
Analiza cómo se deriva la tabla P entre diferentes houses.

### `build_r12_lut.py`
Construye lookup table completa de R12 para rangos de temperatura.

### `r12_lut.py`
Biblioteca para usar la lookup table R12 en código.

**Ejemplo:**
```python
from r12_lut import get_r12, get_temp_from_r12

r12 = get_r12(21.5, house_code=247)
temp, decimals = get_temp_from_r12(0x8BA, house_code=247)
```

### `gen_tramas_thn132n.py`
Genera tramas sintéticas del THN132N para testing.

**Uso:**
```bash
python3 gen_tramas_thn132n.py --temp 20.5 --house 247 --channel 1
```

## Resultados

Los análisis generan archivos markdown y texto con:
- Tablas M y P calculadas
- Estadísticas de precisión por house code
- Comparaciones entre métodos de cálculo
- Lookup tables en formato JSON

## Hallazgos Clave

- **Tabla M**: Universal con 68.26% de precisión (75 temperaturas, -16°C a 61°C)
- **Tabla P Base**: House 3 con 83.76% de precisión
- **Derivación**: Algunas tablas P se derivan mediante XOR de la base
