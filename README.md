# Oregon THN132N - Generador Universal

## 🎯 Inici Ràpid

Aquest projecte conté un generador complet per al protocol Oregon Scientific THN132N basat en investigació exhaustiva.

### Arxius Clau

1. **`esp32/oregon_transmitter_universal.ino`** ⭐ GENERADOR ARDUINO
   - Implementació completa amb fórmules universals
   - LUT optimitzada de P (405 punts, -16°C a +61.4°C)
   - Rolling code configurable
   - 86.79% precisió verificada

2. **`ec40_lut_suite/04_universal_mp_analysis/Docs/`** 📚 DOCUMENTACIÓ
   - `README.md` - Documentació tècnica completa
   - `oregon_p_lut_complete.py` - LUT Python funcional
   - `verification_table.md` - Verificació de 2196 trames

3. **`ESTRUCTURA_PROYECTO.md`** 📖 GUIA D'ESTRUCTURA
   - Mapa complet del projecte
   - Arxius finals vs investigació

## 📦 Descobriments Principals

### 1. Nibble 7: Rolling Code Variable
**Descobriment crític**: El nibble a la posició 7 NO és fix.
- Valors: 0x0, 0x1, 0x2, 0x8
- És un rolling code anti-replay o session ID
- Es manté constant durant una sessió

### 2. R1 i M: Fórmula Universal (100% precisió)
```cpp
sum = sum(nibbles[0:12]);  // Inclou nibble 7!
r1 = (sum & 0xFF) & 0xF;
m = (sum & 0xFF) >> 4;
```

### 3. P: Transformacions XOR Constants (100% verificat)
```cpp
// Transformacions
P(1) = P(0) XOR 0xB
P(2) = P(0) XOR 0x6
P(8) = P(2) XOR 0x7

// Només necessitem 1 LUT base + 3 constants XOR!
```

### 4. Optimització: 83% Reducció Memòria
- **Abans**: 4 LUTs × 600 punts = 2400 bytes
- **Després**: 1 LUT × 405 punts + 4 bytes XOR = 409 bytes

## 🚀 Ús

### Arduino (ESP32)
```cpp
// Configurar a oregon_transmitter_universal.ino
#define DEVICE_ID  247    // House Code (0-255)
#define CHANNEL    1      // 1, 2, o 3
#define ROLLING_CODE 0x2  // 0, 1, 2, o 8

// Compilar i pujar
// El sensor DS18B20 es llegeix automàticament
```

### Python
```python
from ec40_lut_suite.04_universal_mp_analysis.Docs.oregon_p_lut_complete import get_p

# Obtenir P per temperatura i rolling code
p = get_p(20.5, nib7=0x2)
```

## 📊 Verificació

- **Total trames**: 2196
- **Matches**: 1906 (86.79%)
- **Dataset**: ec40_capturas_merged.csv
- **Rang P LUT**: -16.0°C a +61.4°C

## 📂 Estructura del Projecte

```
├── esp32/
│   └── oregon_transmitter_universal.ino    ⭐ GENERADOR FINAL
├── ec40_lut_suite/
│   ├── ec40_capturas_merged.csv           Dataset complet
│   └── 04_universal_mp_analysis/
│       ├── Docs/                          ⭐ DOCUMENTACIÓ
│       │   ├── README.md
│       │   ├── oregon_p_lut_complete.py
│       │   └── verification_table.md
│       └── investigation_scripts/         🔬 Scripts investigació
└── ESTRUCTURA_PROYECTO.md                 📖 Guia detallada
```

## 🔬 Investigació

- **Proves realitzades**: >20,000 algoritmes testats
- **Dataset**: 2196 trames de 8 sensors diferents
- **Rang temporal**: 20/11/2025 - 03/12/2025
- **Documentació completa**: `ec40_lut_suite/04_universal_mp_analysis/Docs/p_algorithm_tests.md`

## 📝 Payload Completo (16 nibbles)

```
Pos  0-3:  EC40           - ID del sensor
Pos  4:    1-3            - Channel
Pos  5-6:  XX XX          - House Code (LSN, MSN)
Pos  7:    0,1,2,8        - Rolling Code ⚠️ VARIABLE!
Pos  8-10: XXX            - Temperatura BCD
Pos  11:   0/8            - Flags (bit 3 = signe)
Pos  12:   X              - R1 (universal: sum & 0xF)
Pos  13:   X              - M (universal: sum >> 4)
Pos  14:   X              - P (LUT + XOR transform)
Pos  15:   X              - Postamble
```

## 🎓 Referències

- **Documentació tècnica**: Ver `ec40_lut_suite/04_universal_mp_analysis/Docs/README.md`
- **Proves detallades**: Ver `ec40_lut_suite/04_universal_mp_analysis/Docs/p_algorithm_tests.md`
- **Historial**: Ver `ec40_lut_suite/05_documentation/`

## 📄 Llicència

Investigació i implementació original.

---

**Versió**: 1.0 Final (2025-12-05)  
**Commit**: 60730c4  
**Autor**: Investigació amb Antigravity AI
