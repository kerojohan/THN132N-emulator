# ESTRATEGIA REVISADA - House IDs Aleatorios

## 🚨 Nueva Realidad

**Los house IDs son ALEATORIOS** y se asignan al reiniciar el sensor.

**Esto cambia TODO:**
- ❌ NO podemos planificar capturar "Houses 3 y 96"
- ❌ NO podemos configurar house IDs específicos
- ✅ Debemos trabajar con CUALQUIER house que salga

## Nueva Estrategia

### 1. Captura Oportunista

**En lugar de elegir houses:**
- Capturar TODO lo que salga
- Usar múltiples sensores simultáneamente
- Reiniciar para obtener nuevos house IDs (si necesario)

### 2. Prioridades Actualizada

#### 🔴 ALTA: Rango Completo de Cualquier House

**Por cada sensor/house que tengas:**
```
- Rango: -10°C a 60°C
- Incremento: 1°C
- Capturas: 3 por temperatura
- Total: ~210 frames por sensor
```

**Objetivo:** Caracterizar COMPLETO cada house que aparezca

#### 🔴 ALTA: Capturas Simultáneas

**2-3 sensores juntos:**
```
- Temperaturas idénticas
- Cualquier house ID que salga
- Comparar transformaciones
- Total: ~350 frames
```

### 3. Análisis Adaptativo

**Con datos aleatorios:**
1. Caracterizar cada nuevo house completo
2. Buscar patrones entre todos los houses
3. Derivar función general por aproximación
4. Interpolar para houses no vistos

## Objetivo Realista

**No buscamos:** Función exacta para cualquier house  
**Buscamos:** Aproximación con >75% precisión

**Con 10-15 houses caracterizados:**
- Identificar familias por nibbles
- Crear lookup table optimizada
- Interpolar para houses intermedios

## Próximo Paso

1. Captura con sensores disponibles (cualquier house ID)
2. Rango más amplio posible
3. Acumular houses hasta tener 10-15 completos
4. Re-analizar patrones globales
