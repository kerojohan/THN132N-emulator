# Oregon Scientific THN132N - Estructura del Projecte

## 📁 Estructura Organitzada

```
Antigravity/
├── docs/ 📚 Documentació general
│   ├── general/
│   │   ├── Documentació Final.md
│   │   ├── METODOLOGIA_DETALLADA.md          📖 Metodologia científica
│   │   ├── Oregon_THN132N_BAR206.pdf
│   │   └── Oregon_THN132N_Protocol_Analysis.md
│   └── easyeda/                            📐 PCB i esquemes
│
├── firmware/
│   ├── esp32/
│   │   ├── oregon_transmitter_universal.ino  ⭐ GENERADOR FINAL
│   │   └── oregon_transmitter.ino            (versió amb LUTs)
│   └── attiny/
│       ├── attiny85THN132N.ino
│       └── attiny85THN132N_aht20.ino
│
├── analysis/
│   ├── ec40_capturas_merged.csv          📊 Dataset (2196 trames)
│   ├── oregon_p_table_247.h              LUT empírica
│   │
│   └── 04_universal_mp_analysis/
│       ├── Docs/ ⭐ DOCUMENTACIÓ TÈCNICA
│       │   ├── README.md                 Guia tècnica
│       │   ├── oregon_p_lut_complete.py  LUT funcional
│       │   ├── verification_table.md     Verificació
│       │   ├── verification_table.csv    Dades verificació
│       │   └── p_algorithm_tests.md      >20k proves
│       │
│       └── investigation_scripts/        🔬 Scripts proves
│           └── README.md
│
├── README.md ⭐ INICI AQUÍ
├── derivados/
│   └── hx711-2/
├── logs/
│   └── tuning_log.csv
└── ESTRUCTURA_PROYECTO.md (aquest document)
```

## ⭐ ARXIUS CLAU - COMENÇAR AQUÍ

### 1. Implementació Arduino (RECOMANAT)
**`firmware/esp32/oregon_transmitter_universal.ino`**
- Generador complet amb fórmules universals
- Inclou LUT de P optimitzada (405 punts)
- Transformacions XOR per rolling codes
- 86.79% precisió verificada

### 2. Documentació General
**`docs/general/`** - Carpeta arrel
- `Documentació Final.md` - Document final del projecte
- `METODOLOGIA_DETALLADA.md` - Metodologia científica completa
- `Oregon_THN132N_Protocol_Analysis.md` - Anàlisi protocol
- `Oregon_THN132N_BAR206.pdf` - PDF tècnic

### 3. Documentació Tècnica
**`analysis/04_universal_mp_analysis/Docs/`**
- `README.md` - Guia tècnica completa
- `oregon_p_lut_complete.py` - LUT Python funcional
- `verification_table.md/.csv` - Verificació 2196 trames
- `p_algorithm_tests.md` - >20,000 proves documentades
**`analysis/04_universal_mp_analysis/Docs/oregon_p_lut_complete.py`**
- LUT completa de P (405 punts)
- Funció `get_p(temp_celsius, nib7)`
- Taula de transformacions XOR

### 4. Verificació
**`analysis/04_universal_mp_analysis/Docs/verification_table.md`**
- Comparació 2196 trames capturades vs generades
- Estadístiques per House i Rolling Code
- Anàlisi d'errors

## 🔬 Arxius d'Investigació

Tots els scripts a `analysis/04_universal_mp_analysis/` són part del procés d'investigació:

### Scripts d'Anàlisi (NO necessaris per usar)
- `analyze_*.py` - Anàlisi de patrons
- `solve_*.py` - Proves d'algorismes (>20,000 variants)
- `test_*.py` - Tests de verificació
- `brute_force_*.py` - Cerca exhaustiva

Aquests scripts van ser necessaris per arribar a la solució però **NO cal executar-los** per utilitzar el generador final.

## 🚀 Ús Ràpid

### Opció 1: Arduino (Recomanat)
1. Obre `firmware/esp32/oregon_transmitter_universal.ino`
2. Configura `DEVICE_ID`, `CHANNEL`, `ROLLING_CODE`
3. Compila i puja a ESP32
4. Connecta DS18B20 al pin configurat

### Opció 2: Python
```python
from oregon_p_lut_complete import get_p

# Exemple
temp_c = 20.5
nib7 = 0x2
p = get_p(temp_c, nib7)
```

## 📊 Descobriments Clau

1. **Nibble 7**: Rolling code variable (0, 1, 2, 8) - NO fix com es pensava
2. **R1 i M**: Fórmula universal `sum(nibbles[0:12]) & 0xFF` - 100% precisió
3. **P**: Transformacions XOR constants:
   - P(1) = P(0) XOR 0xB
   - P(2) = P(0) XOR 0x6
   - P(8) = P(2) XOR 0x7

## 📝 Historial d'Investigació

Consulta `analysis/05_documentation/` per veure documents històrics del procés d'investigació.

## ❓ Suport

- **Documentació tècnica**: `analysis/04_universal_mp_analysis/Docs/README.md`
- **Proves detallades**: `analysis/04_universal_mp_analysis/Docs/p_algorithm_tests.md`
- **Verificació**: `analysis/04_universal_mp_analysis/Docs/verification_table.md`

---

**Versió**: Final 2025-12-05  
**Precisió**: 86.79% (2196 trames verificades)  
**Optimització**: 83% reducció memòria vs LUTs originals
