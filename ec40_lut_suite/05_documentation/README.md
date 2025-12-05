# 05 - Documentation / Documentación

Documentos con análisis, conclusiones y resultados de la investigación del protocolo Oregon THN132N.

## 📄 Documentos Principales

### `ANALISIS_CORRELACION_HOUSES.md`
Análisis completo de la correlación entre house IDs y tablas de codificación.

**Contenido:**
- Análisis con 2197 tramas de 8 house IDs
- Descubrimiento del XOR constante 0x075
- Tabla M universal vs tablas P específicas
- Recomendaciones para investigación futura

### `CONCLUSION_FINAL.md`
Conclusiones finales del proyecto de análisis del protocolo.

**Hallazgos clave:**
- Estructura del mensaje EC40
- Tablas M y P calculadas
- Método de codificación R12
- Validación empírica

### `RESUMEN_TABLAS_M_P.md`
Resumen consolidado de todas las tablas M y P encontradas.

**Incluye:**
- Tablas por house code
- Comparaciones entre houses
- Estadísticas de precisión
- Métodos de cálculo

## 📊 Documentos Técnicos

### `tablas_M_P_por_sensor.md`
Tablas M y P calculadas individualmente para cada sensor/house.

**Formato:**
```markdown
## House X (0xNN)
### Tabla P: [...]
### Tabla M: {...}
### Precisión: XX.XX%
```

### `tablas_M_P_recalculadas.md`
Resultados de recalcular tablas con algoritmos mejorados.

### `tablas_M_P_universales.md`
Tablas calculadas combinando todos los datos de todos los houses.

**Resultado:**
- Tabla M: 75 temperaturas, 68.26% precisión
- Tabla P base: House 3, 83.76% precisión

### `README_LUT.txt`
Documentación sobre las lookup tables R12.

## 🎯 Hallazgos Clave Documentados

### 1. Byte3 y House Code
```
b3_high = (house_code >> 4) & 0x0F
```
Confirmado con 100% de verificación en 8 houses.

### 2. Transformación XOR
```python
# House 247 = House 3 XOR 0x075
P_247 = [p ^ 0x075 for p in P_BASE]
```
Confirmado con XOR constante perfecto.

### 3. Tabla M Universal
```python
M_TABLE = {
    -16: 0x2D4, -15: 0x227, -14: 0x276, ..., 61: 0x14F
}
```
68.26% de precisión global en 2174 tramas.

### 4. Tabla P Base
```python
P_BASE = [0x075, 0x000, 0x09F, 0x0EA, 0x0C0, 
          0x0B5, 0x02A, 0x05F, 0x01E, 0x06B]
```
House 3 como referencia con 83.76% de precisión.

## 📈 Precisión por House Code

| House | Hex | Precisión | Tramas | Estado |
|-------|-----|-----------|--------|--------|
| 0 | 0x00 | 100% | 4 | ✅ Perfecto |
| 3 | 0x03 | 83.76% | 468 | ⭐ Tabla base |
| 92 | 0x5C | 100% | 2 | ✅ Perfecto |
| 96 | 0x60 | 42.53% | 174 | ⚠️ Patrón especial |
| 135 | 0x87 | 100% | 6 | ✅ Perfecto |
| 247 | 0xF7 | 66.36% | 1516 | ✅ XOR 0x075 |
| 251 | 0xFB | - | 2 | Pocos datos |

## 🔬 Metodología

Todos los análisis siguen este proceso:

1. **Captura de datos reales** con sensores THN132N
2. **Extracción de R12** de tramas decodificadas
3. **Cálculo iterativo** de tablas M y P
4. **Validación cruzada** con datos independientes
5. **Documentación de resultados** y precisiones

## 📖 Lecturas Recomendadas

**Para empezar:**
1. `CONCLUSION_FINAL.md` - Resumen ejecutivo
2. `RESUMEN_TABLAS_M_P.md` - Tablas consolidadas

**Para análisis profundo:**
3. `ANALISIS_CORRELACION_HOUSES.md` - Correlaciones
4. `tablas_M_P_universales.md` - Tabla universal

**Para implementación:**
5. `/04_utilities/README.md` - API de codificación
6. `README_LUT.txt` - Uso de lookup tables

## 🚀 Próximos Pasos

Basados en los análisis documentados:

1. **Completar función XOR mask**
   - Determinar patrón para todos los houses
   - Validar con más capturas

2. **Mejorar tabla M**
   - Investigar el 31.74% de errores
   - ¿Varía M también por house?

3. **Caracterizar House 96**
   - Entender valores repetidos en tabla P
   - Mejorar precisión del 42.53%

4. **Houses perfectos**
   - Analizar houses 0, 92, 135
   - ¿Por qué tienen 100% con tabla base?

## 📝 Convenciones de Documentación

- **Formato:** Markdown para facilidad de lectura
- **Código:** Bloques con sintaxis Python
- **Tablas:** Formato markdown para comparaciones
- **Resultados:** Siempre con precisiones y tamaños de muestra
- **Referencias:** Links a archivos y funciones relevantes

## 🔗 Enlaces Útiles

- Raíz del proyecto: `/ec40_lut_suite/`
- Scripts de análisis: `/03_house_correlation/`
- Utilidades: `/04_utilities/`
- Datos: `/ec40_capturas_merged.csv`
