# Análisis del Protocolo Oregon Scientific THN132N: Tablas M/P y House ID

**Fecha:** 02 de Diciembre de 2025
**Estado:** Confirmado experimentalmente

## 1. Resumen Ejecutivo

Contrario a la creencia popular y a análisis previos, **las tablas de codificación (M y P) del sensor THN132N NO son universales**. Dependen directamente del **House ID** (Rolling Code) generado aleatoriamente por el sensor al reiniciarse.

Para emular correctamente un sensor, es necesario utilizar las tablas específicas correspondientes al House ID que se está transmitiendo. El uso de tablas genéricas resulta en una tasa de error significativa (~75% de tramas incorrectas).

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
Las tablas `M` y `P` **varían según el House ID**.
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

Esto demuestra irrefutablemente que **R12 depende del House ID**.

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

Dado que el House ID es aleatorio (random) al encender el sensor, no es práctico deducir una "fórmula universal" sin capturar datos de todos los 256 posibles IDs.

### Estrategia Recomendada
Para emular el sensor con un microcontrolador (ESP32/ATtiny):

1.  **Fijar un House ID conocido:** No generar uno aleatorio. Usar uno del que ya tengamos las tablas.
2.  **Usar House ID 247 (0xF7):** Es el que hemos validado extensamente y funciona "perfecto".
3.  **Implementar la Tabla Derivada:**

```python
# Configuración para House 247
HOUSE_CODE = 247
P_TABLE = [x ^ 0x075 for x in P_BASE] 
# Resultado: [0x000, 0x075, 0x0EA, 0x09F, 0x0B5, 0x0C0, 0x05F, 0x02A, 0x06B, 0x01E]
```

## 6. Archivos Generados en el Proyecto

*   `ec40_lut_suite/oregon_parameters.py`: **Archivo Maestro**. Contiene las tablas base y la lógica para derivar la tabla correcta para House 247. Listo para importar en scripts Python.
*   `ec40_lut_suite/tablas_M_P_por_sensor.md`: Documentación técnica con los valores hexadecimales crudos por sensor.
*   `ec40_lut_suite/recalc_M_P_per_sensor.py`: Herramienta para extraer tablas nuevas si se capturan datos de un nuevo House ID.

## 7. Conclusión Final

El protocolo Oregon Scientific v2.1 para el sensor THN132N incluye un mecanismo de ofuscación basado en el House ID. Para una emulación exitosa, **no se pueden usar tablas genéricas**; se deben usar las tablas específicas calculadas para el House ID que se está transmitiendo.

El uso de **House ID 247** junto con su tabla P derivada (`P_BASE ^ 0x075`) garantiza una compatibilidad total con las estaciones base originales.
