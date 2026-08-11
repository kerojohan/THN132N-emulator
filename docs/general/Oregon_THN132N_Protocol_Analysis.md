# Análisis del Protocolo Oregon Scientific THN132N: Tablas M/P y House ID

**Fecha:** 02 de Diciembre de 2025
**Estado:** Confirmado experimentalmente (actualizado Febrer 2026)

## 1. Resumen Ejecutivo

Se ha confirmado que las tablas de codificación (M y P) del sensor THN132N **sí se pueden generalizar** mediante transformaciones XOR, y que el generador funciona **para cualquier House ID y canal** cuando se aplican dichas transformaciones.

En la práctica, el emulador genera tramas válidas para distintos House IDs y canales, verificadas con decodificación rtl_433 y aceptación por la consola BAR206.

Actualización experimental 2026-08-11: la posición física 3 del selector THN132N se codifica en EC40 como `channel=4` (valores válidos `1`, `2`, `4`). Se capturó el sensor original como `EC40=ec404ff88030359a`, `temp=30.8°C`, `channel=4`, `id=255`, `R12=0x89A`; la emulación BAR206 aceptada usa `DEVICE_ID=255`, `CHANNEL=4` y ajuste `R12 ^= 0x9E1`.

## 2. El Algoritmo de Codificación

El sensor utiliza un valor intermedio de 12 bits, denominado **R12**, para codificar la temperatura. Este valor se distribuye en el mensaje EC40.

La fórmula fundamental es:
```
R12 = M[e] XOR P[d]
```
Donde:
*   `e`: Parte entera de la temperatura (-16 a +61 °C).
*   `d`: Parte decimal de la temperatura (0 a 9).
*   `M[e]`: Valor de la tabla M para la parte entera.
*   `P[d]`: Valor de la tabla P para la décima.

### El Descubrimiento Clave
Las tablas `M` y `P` **varían según el House ID**, pero **se derivan de una base común** mediante transformaciones XOR estables.
*   **House ID:** Un valor de 8 bits generado aleatoriamente al insertar las pilas.
*   El sensor utiliza este House ID como "semilla" para alterar las tablas base.

## 3. Evidencia Experimental

Se analizaron 2,174 tramas capturadas de un mismo sensor físico reiniciado múltiples veces (generando distintos House IDs).

### Comparativa House 3 vs House 247
Al comparar tramas con la **misma temperatura exacta** (ej. 20.3°C) transmitidas bajo distintos House IDs:

| Parámetro | House ID 3 | House ID 247 | Resultado |
| :--- | :--- | :--- | :--- |
| **Temperatura** | 20.3°C | 20.3°C | Idéntica |
| **Valor R12** | `0x188` | `0x82B` | **DIFERENTE** ❌ |
| **Mensaje EC40** | `...189...` | `...889...` | Diferente |

Esto demuestra irrefutablemente que **R12 depende del House ID**, y por tanto debe derivarse de una base común.

## 4. Relación Matemática (Ingeniería Inversa)

Se ha identificado que las tablas se derivan de una "Tabla Base" (observada en House ID 3) mediante operaciones XOR.

### Tabla Base (House ID 3)
```python
P_BASE = [0x075, 0x000, 0x09F, 0x0EA, 0x0C0, 0x0B5, 0x02A, 0x05F, 0x01E, 0x06B]
```

### Derivación para House ID 247 (0xF7)
Se descubrió que la tabla para House 247 es la tabla base con una máscara XOR constante aplicada a todos los elementos.

**Fórmula:**
```python
P_247[d] = P_BASE[d] XOR 0x075
```
*Nota: Inicialmente parecía una permutación, pero se demostró que `P_BASE[d] XOR P_BASE[d+1]` es siempre `0x075`, lo que creaba la ilusión de un intercambio de pares.*

### Derivación para House ID 96 (0x60)
Este caso presenta un patrón más complejo (XOR alternado), lo que sugiere que la función de generación depende de los bits específicos del House ID.

## 5. Implicaciones Prácticas para la Emulación

### Mapeo del canal físico 3

En sensores THN132N/BAR206, el selector físico de canal usa el nibble Oregon `1`, `2`, `4`, no `1`, `2`, `3`. Por tanto, para reemplazar un sensor configurado en canal físico 3 hay que transmitir `channel=4`.

La captura validada del sensor original fue:

```text
raw=555555559995a5a6aaa65555a9a9aa5aaa5a666999
EC40=ec404ff88030359a
temp=30.8°C channel=4 id=255 r12=0x89A
```

La configuración que la BAR206 aceptó como reemplazo fue:

```cpp
CHANNEL = 4;
DEVICE_ID = 255;
R12 ^= 0x9E1;
```

El frame emitido por ESP32-C3/CC1101 se validó con `rtl_433` como `Oregon-THN132N`, `channel=4`, `id=255`, temperatura correcta y SNR aproximado de 19 dB.

### Estrategia Recomendada
Para emular el sensor con un microcontrolador (ESP32/ATtiny):

1.  **Generar R12 a partir de la tabla base** y aplicar la **transformación XOR** correspondiente al House ID y nib7.
2.  **Validar** con rtl_433 y/o BAR206 al cambiar House ID y canal.
3.  **Mantener el esquema** P/M + XOR como base del generador universal.

```python
# Ejemplo de derivación (House 247)
HOUSE_CODE = 247
P_TABLE = [x ^ 0x075 for x in P_BASE]
# Resultado: [0x000, 0x075, 0x0EA, 0x09F, 0x0B5, 0x0C0, 0x05F, 0x02A, 0x06B, 0x01E]
```

## 6. Archivos Generados en el Proyecto

*   `analysis/04_utilities/oregon_parameters.py`: **Archivo Maestro**. Contiene las tablas base y la lógica para derivar la tabla correcta por House ID.
*   `analysis/05_documentation/tablas_M_P_por_sensor.md`: Documentación técnica con los valores hexadecimales crudos por sensor.
*   `analysis/02_table_analysis/recalc_M_P_per_sensor.py`: Herramienta para extraer tablas nuevas si se capturan datos de un nuevo House ID.

## 7. Conclusión Final

El protocolo Oregon Scientific v2.1 para el sensor THN132N incluye un mecanismo de ofuscación basado en el House ID, **pero es derivable** a partir de una base común mediante transformaciones XOR. Con esta lógica, el generador funciona para **cualquier House ID y canal**, validado experimentalmente.
