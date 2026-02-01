# EC40 LUT Suite - Estructura de Carpetas

Este directorio contiene todos  los scripts y documentación relacionados con el análisis del protocolo Oregon Scientific THN132N (EC40).

## 📁 Estructura

### `01_data_capture/` - Captura y Procesamiento de Datos
Scripts para capturar, registrar y procesar tramas del sensor.

**Scripts:**
- `logger_ec40.py` - Logger para capturar tramas en tiempo real
- `merge_ec40_csvs.py` - Fusionar múltiples archivos CSV de capturas

**Datasets:**
- `ec40_live.csv` - Capturas en tiempo real (raíz)
- `ec40_capturas_merged.csv` - Dataset consolidado con 2197 tramas (raíz)

### `02_table_analysis/` - Análisis de Tablas M y P
Scripts para calcular y analizar las tablas de codificación M y P.

**Scripts:**
- `calc_M_desde_csv.py` - Calcular tabla M desde capturas CSV
- `calc_universal_tables.py` - Calcular tablas universales combinadas
- `recalc_M_P_per_sensor.py` - Recalcular tablas por sensor individual
- `recalc_M_P_tables.py` - Recalcular tablas M y P general
- `analyze_p_derivation.py` - Análisis de derivación de tabla P
- `build_r12_lut.py` - Construir lookup table R12
- `r12_lut.py` - Biblioteca de lookup table R12
- `use_r12_lut_example.py` - Ejemplo de uso de R12 LUT
- `gen_tramas_thn132n.py` - Generador de tramas sintéticas

**Outputs:**
- `r12_lut.json` - Lookup table R12 en formato JSON (raíz)

### `03_house_correlation/` - Correlación entre House IDs
Scripts para analizar la relación entre house codes y las tablas de codificación.

**Scripts principal:**
- `investigate_xor_mask_function.py` ⭐ - Investigación de función XOR mask general
- `analyze_xor_pattern.py` - Análisis detallado del patrón XOR 0x075
- `test_universal_tables.py` - Prueba de hipótesis de tablas universales

**Scripts de análisis:**
- `analyze_byte3_house.py` - Relación byte3 ↔ house code
- `analyze_house_r12.py` - Análisis de R12 por house code
- `analyze_multi_house.py` - Comparación entre múltiples houses

**Hallazgos clave:**
- ✅ b3_high = (house_code >> 4) & 0x0F
- ✅ Houses 3 y 247: XOR constante 0x075
- ✅ Tabla M universal (68.26% precisión)
- ✅ Tabla P base (House 3)

### `04_utilities/` - Utilidades y Bibliotecas
Módulos reutilizables para codificación/decodificación.

**Biblioteca principal:**
- `oregon_parameters.py` - Parámetros y funciones de codificación EC40

**Funciones disponibles:**
```python
from oregon_parameters import calculate_r12, encode_ec40_bytes, get_p_table

# Calcular R12 para una temperatura
r12 = calculate_r12(21.5, house_code=247)

# Generar bytes EC40
byte3, byte7 = encode_ec40_bytes(21.5, house_code=247, channel=1)

# Obtener tabla P para un house code
p_table = get_p_table(247)
```

### `05_documentation/` - Documentación y Resultados
Documentos con análisis, conclusiones y resultados de investigación.

**Documentos principales:**
- `ANALISIS_CORRELACION_HOUSES.md` - Análisis de correlación house IDs
- `CONCLUSION_FINAL.md` - Conclusiones finales del proyecto
- `RESUMEN_TABLAS_M_P.md` - Resumen de tablas M y P

**Documentos técnicos:**
- `tablas_M_P_por_sensor.md` - Tablas calculadas por sensor
- `tablas_M_P_recalculadas.md` - Tablas recalculadas
- `tablas_M_P_universales.md` - Tablas universales
- `README_LUT.txt` - Documentación de lookuptables

## 🎯 Flujo de Trabajo Típico

### 1. Captura de Datos
```bash
cd 01_data_capture
python3 logger_ec40.py  # Capturar tramas en tiempo real
python3 merge_ec40_csvs.py  # Consolidar capturas
```

### 2. Análisis de Tablas
```bash
cd 02_table_analysis
python3 calc_universal_tables.py ../ec40_capturas_merged.csv
python3 recalc_M_P_tables.py ../ec40_capturas_merged.csv
```

### 3. Análisis de Correlación
```bash
cd 03_house_correlation
python3 investigate_xor_mask_function.py ../ec40_capturas_merged.csv
python3 analyze_multi_house.py ../ec40_capturas_merged.csv
```

### 4. Uso en Aplicación
```python
# En tu código
import sys
sys.path.append('/path/to/analysis/04_utilities')
from oregon_parameters import calculate_r12, encode_ec40_bytes

# Usar las funciones
r12 = calculate_r12(temperatura, house_code)
```

## 📊 Datasets Disponibles

| Archivo | Tramas | Houses | Rango Temp | Descripción |
|---------|--------|--------|------------|-------------|
| `ec40_live.csv` | ~120 | 6-8 | 18-23°C | Capturas recientes |
| `ec40_capturas_merged.csv` | 2197 | 8 | -16 a 61°C | Dataset completo consolidado |

## 🔬 Resultados Clave

### Tabla P Base (House 3)
```python
P_BASE = [0x075, 0x000, 0x09F, 0x0EA, 0x0C0, 
          0x0B5, 0x02A, 0x05F, 0x01E, 0x06B]
```

### Transformación XOR
```python
# House 247 = House 3 XOR 0x075
P_247 = [p ^ 0x075 for p in P_BASE]
```

### Tabla M Universal
75 temperaturas de -16°C a 61°C con 68.26% de precisión global.

## 📖 Documentación Adicional

Ver `/05_documentation/` para análisis detallados y conclusiones.

## 🚀 Próximos Pasos

1. Completar función `calculate_xor_mask()` para todos los houses
2. Capturar más datos de houses con patrones no claros
3. Validar tabla M universal con más houses
4. Implementar decodificador completo

## 📝 Notas

- Todos los scripts aceptan rutas CSV como argumento
- Por defecto buscan `ec40_capturas_merged.csv` en el directorio raíz
- Los resultados se guardan en archivos `.txt` o `.md` en la misma carpeta
