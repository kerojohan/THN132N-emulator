# Resumen Ejecutivo - Datos Necesarios

## 🎯 Objetivo
Capturar datos adicionales para derivar tablas M y P de cualquier house ID mediante función universal.

## 📊 Estado Actual

**Confirmado:**
- ✅ Tabla P: XOR 0x075 (Houses 3↔247)
- ✅ Tabla M: XOR condicional 3↔96 (solo 26-33°C)

**Falta:**
- ❌ Patrón tabla M fuera de 26-33°C
- ❌ Transformación Houses 3↔247 y 96↔247
- ❌ Validación houses 0, 92, 135

## 📋 Datos Prioritarios

### 🔴 Alta Prioridad (~900 frames)

1. **Extender rango Houses 3↔96** (300 frames)
   - Temperaturas: -10 a 25°C y 34 a 60°C
   - Validar si XOR sigue siendo condicional

2. **Caracterizar Houses 3↔247** (150 frames)
   - Buscar XOR condicional por rangos
   - Temperaturas idénticas en ambos houses

3. **Validar Houses 0, 92, 135** (450 frames)
   - Confirmar si usan tabla base (XOR=0)
   - Ampliar de 2-6 frames a mínimo 150 cada uno

### 🟡 Media Prioridad (~1140 frames)

4. **House 96 completo** (600 frames)
   - Entender tabla P con valores repetidos

5. **Houses adicionales** (540 frames)
   - 9 houses nuevos para buscar familias
   - Variedad de nibbles altos y bajos

### 🟢 Baja Prioridad (~450 frames)

6. **Temperaturas extremas** (150 frames)
7. **Verificación décimas** (300 frames)

## 🔬 Método de Captura

**Configuración:**
- 2-3 sensores simultáneos (mismo ambiente)
- Houses target: 3, 96, 247, 0, 92, 135
- Temperatura controlada (-20 a 70°C)

**Por temperatura:**
- Mínimo 3 capturas
- Temperatura estable (±0.1°C)
- Validar ausencia de outliers

## ✅ Criterio de Éxito

Poder implementar:
```python
def calculate_p_table(house_code) -> List[int]
def calculate_m_table(house_code, temp_range) -> Dict[int, int]
```

Con **>90% precisión** para cualquier house ID.

---

**Total estimado:** ~2490 frames adicionales
**Ver:** `plan_captura_datos.md` para detalles completos
