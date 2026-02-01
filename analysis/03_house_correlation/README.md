# 03 - House Correlation / Correlación House IDs

Análisis de la relación entre house codes y las tablas de codificación M y P.

## 🎯 Objetivo

Determinar si las tablas M y P son:
- Universales para todos los sensores
- Específicas de cada sensor físico
- Derivables mediante función del house code

## Scripts de Investigación

### ⭐ `investigate_xor_mask_function.py`
**Script principal** para investigar la función general de transformación XOR.

**Uso:**
```bash
python3 investigate_xor_mask_function.py ../ec40_capturas_merged.csv
```

**Output:**
- Tablas P por house code
- Análisis de XOR masks
- Propuesta de función `calculate_xor_mask()`

### `analyze_xor_pattern.py`
Análisis detallado del patrón XOR 0x075 entre Houses 3 y 247.

**Hallazgo:** 
```python
P_247 = [p ^ 0x075 for p in P_3]  # Transformación exacta
```

### `test_universal_tables.py`
Prueba la hipótesis de que existe una tabla universal.

**Resultados:**
- Dataset pequeño (111 tramas): 34.91% precisión ❌
- Dataset ampliado (2197 tramas): 68.26% precisión ⭐

## Scripts de Análisis

### `analyze_byte3_house.py`
Analiza la relación entre el house code y el byte 3 del mensaje EC40.

**Descubrimiento confirmado:**
```python
b3_high = (house_code >> 4) & 0x0F  # 100% verificado
```

### `analyze_house_r12.py`
Analiza cómo varía R12 según el house code para misma temperatura.

### `analyze_multi_house.py`
Compara tablas M y P entre múltiples house codes buscando patrones.

**Output:**
- Comparación de precisiones
- Análisis de transformaciones XOR
- Temperaturas comunes entre houses

## 🔬 Hallazgos Principales

### 1. Estructura de Byte3
```
byte3 = [house_high:4bits][R12_high:4bits]
```
Confirmado con 8 house codes diferentes.

### 2. XOR Constante Houses 3 ↔ 247
```python
P_BASE = [0x075, 0x000, 0x09F, 0x0EA, 0x0C0, 0x0B5, 0x02A, 0x05F, 0x01E, 0x06B]
P_247  = [0x000, 0x075, 0x0EA, 0x09F, 0x0B5, 0x0C0, 0x05F, 0x02A, 0x06B, 0x01E]

# Para toda décima d:
P_247[d] = P_BASE[d] ^ 0x075
```

### 3. Permutación de Valores
Ambas tablas contienen los **mismos 10 valores**, solo reordenados con intercambio de pares.

### 4. Precisión con Tabla Base

| House | Precisión | Tramas | Notas |
|-------|-----------|--------|-------|
| 0 | 100% | 4 | Perfecto |
| 3 | 83.76% | 468 | **Base** |
| 92 | 100% | 2 | Perfecto |
| 135 | 100% | 6 | Perfecto |
| 247 | 66.36% | 1516 | XOR 0x075 |
| 96 | 42.53% | 174 | Patrón especial |

### 5. Tabla M Universal
68.26% de precisión global - sugiere que M es independiente del house code.

## 📊 Función Propuesta

```python
def calculate_xor_mask(house_code):
    """Calcula XOR mask para derivar tabla P."""
    if house_code == 3:
        return 0x000  # Tabla base, sin transformación
    elif house_code == 247:
        return 0x075  # Confirmado empíricamente
    else:
        # Por determinar - necesitamos más datos
        return None
```

## 🚧 Pendiente de Investigar

1. **Houses con 100% precisión** (0, 92, 135)
   - ¿Comparten tabla base directamente?
   - ¿Qué tienen en común?

2. **House 96** (42.53% precisión)
   - Tabla con valores repetidos
   - Comportamiento diferente

3. **Función general**
   - Relación entre house code y XOR mask
   - ¿Depende del nibble bajo?
   - ¿Familias de houses con mismo patrón?

## 📖 Documentación

Ver `/05_documentation/ANALISIS_CORRELACION_HOUSES.md` para análisis completo.

## ✅ Conclusión

**Las tablas NO son completamente independientes.** Existe una tabla base (House 3) y función de transformación XOR que deriva otras tablas.

Esto simplifica la implementación:
- Solo almacenar tabla base
- Derivar tablas específicas con XOR
- Tabla M es universal
