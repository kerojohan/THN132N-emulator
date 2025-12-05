# Oregon Scientific THN132N Protocol Decoding

Proyecto de análisis y decodificación del protocolo de comunicación del sensor de temperatura Oregon Scientific THN132N (protocolo EC40).

## 🎯 Objetivo

Entender completamente el protocolo de codificación del sensor THN132N para poder:
- Decodificar tramas capturadas
- Generar tramas sintéticas para emular el sensor
- Crear transmisores compatibles con receptores Oregon Scientific

## 📁 Estructura del Proyecto

### `/ec40_lut_suite/` - ⭐ Suite de Análisis Principal

Suite completa organizada en 5 categorías. **Ver [`ec40_lut_suite/README.md`](ec40_lut_suite/README.md) para documentación completa.**

### Otras Carpetas

- `/esp32/` - Implementaciones ESP32
- `/attiny/` - Implementaciones ATtiny85
- `/Docs/` - Documentación técnica

## 🔬 Hallazgos Principales

### XOR Constante Houses 3 ↔ 247
```python
P_247 = [p ^ 0x075 for p in P_BASE]  # Transformación exacta
```

### Tabla M Universal
68.26% precisión global (75 temperaturas, -16°C a 61°C)

### Precisión por House
- Houses 0, 92, 135: **100%** con tabla base
- House 3: **83.76%** (tabla base)
- House 247: 66.36% (XOR 0x075)

Ver documentación completa en `/ec40_lut_suite/` para detalles.
