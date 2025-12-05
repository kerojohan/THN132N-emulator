# 04 - Utilities / Utilidades

Módulos reutilizables para codificación y decodificación del protocolo Oregon THN132N (EC40).

## Módulo Principal

### `oregon_parameters.py`
Biblioteca con parámetros, tablas y funciones de codificación EC40.

## Funciones Disponibles

### `get_p_table(house_code)`
Obtiene la tabla P correcta para un house code dado.

```python
from oregon_parameters import get_p_table

# Obtener tabla P para House 247
p_table = get_p_table(247)
# Retorna: [0x000, 0x075, 0x0EA, 0x09F, 0x0B5, 0x0C0, 0x05F, 0x02A, 0x06B, 0x01E]
```

**Houses soportados:**
- House 3: Tabla base
- House 247: Tabla base XOR 0x075
- House 96: Patrón especial
- Otros: Retorna tabla base con advertencia

### `calculate_r12(temp_c, house_code)`
Calcula el valor R12 para una temperatura y house code dados.

```python
from oregon_parameters import calculate_r12

# Calcular R12 para 21.5°C con House 247
r12 = calculate_r12(21.5, house_code=247)
print(f"R12 = 0x{r12:03X}")
# Output: R12 = 0x8CF (ejemplo)
```

**Parámetros:**
- `temp_c`: Temperatura en °C
- `house_code`: Código del house (default: 247)

**Returns:** Valor R12 de 12 bits

**Lanza:** `ValueError` si temperatura fuera de rango

### `encode_ec40_bytes(temp_c, house_code, channel)`
Genera los bytes clave del mensaje EC40.

```python
from oregon_parameters import encode_ec40_bytes

# Generar bytes para mensaje EC40
byte3, byte7 = encode_ec40_bytes(21.5, house_code=247, channel=1)

print(f"Byte 3: 0x{byte3:02X}")  # Contiene house_high + R12_high
print(f"Byte 7: 0x{byte7:02X}")  # Contiene R12_low
```

**Parámetros:**
- `temp_c`: Temperatura en °C
- `house_code`: Código del house (default: 247)
- `channel`: Canal del sensor 1-3 (default: 1)

**Returns:** Tupla `(byte3, byte7)`

## Estructura de Byte3 y Byte7

### Byte 3
```
[7:4] = house_high (nibble alto del house code)
[3:0] = R12_high (nibble alto de R12)
```

### Byte 7
```
[7:0] = R12_low (byte bajo de R12)
```

### Reconstrucción de R12
```python
R12 = ((byte3 & 0x0F) << 8) | byte7
```

## Constantes Disponibles

```python
DEFAULT_HOUSE_CODE = 247  # House code por defecto
DEFAULT_CHANNEL = 1        # Canal por defecto

P_TABLE_BASE = [  # Tabla P base (House 3)
    0x075, 0x000, 0x09F, 0x0EA, 0x0C0,
    0x0B5, 0x02A, 0x05F, 0x01E, 0x06B
]

M_TABLE = {  # Tabla M (universal)
    -16: 0x2D4, -15: 0x227, ..., 61: 0x14F
}
```

## Ejemplo Completo

```python
#!/usr/bin/env python3
from oregon_parameters import calculate_r12, encode_ec40_bytes

# Configuración
temperatura = 21.5
house_code = 247
channel = 1

# Calcular R12
r12 = calculate_r12(temperatura, house_code)
print(f"Temperatura: {temperatura}°C")
print(f"R12: 0x{r12:03X}")

# Generar bytes del mensaje
byte3, byte7 = encode_ec40_bytes(temperatura, house_code, channel)
print(f"Byte 3: 0x{byte3:02X}")
print(f"Byte 7: 0x{byte7:02X}")

# Verificar reconstrucción
r12_reconstructed = ((byte3 & 0x0F) << 8) | byte7
print(f"R12 reconstruido: 0x{r12_reconstructed:03X}")
assert r12 == r12_reconstructed, "Error en reconstrucción"
```

## Integración en Proyectos

### Opción 1: Copia directa
```bash
cp oregon_parameters.py /tu/proyecto/
```

### Opción 2: Agregar al PATH de Python
```python
import sys
sys.path.append('/path/to/ec40_lut_suite/04_utilities')
from oregon_parameters import calculate_r12
```

### Opción 3: Instalación como paquete
```bash
cd ec40_lut_suite/04_utilities
pip install -e .  # Si se crea setup.py
```

## Notas de Implementación

- La tabla M es universal (válida para todos los houses)
- Las tablas P se derivan de tabla base mediante XOR
- Solo se han caracterizado completamente houses 3, 96 y 247
- Para otros houses, usar tabla base con precaución

## Validación

Todas las funciones han sido validadas con:
- 2197 tramas reales
- 8 house codes diferentes  
- Rango de -16°C a 61°C
- Precisión global: 68.26%
