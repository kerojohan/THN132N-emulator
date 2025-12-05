# Taula de Verificació - Captures vs Generador

**Total trames**: 2196
**Matches**: 1906 (86.79%)
**Errors**: 290

## Estadístiques per House

| House | Total | Matches | Errors | Precisió |
|-------|-------|---------|--------|----------|
| 0 | 4 | 2 | 2 | 50.0% ❌ |
| 3 | 472 | 324 | 148 | 68.6% ❌ |
| 79 | 2 | 2 | 0 | 100.0% ✅ |
| 92 | 2 | 2 | 0 | 100.0% ✅ |
| 96 | 174 | 42 | 132 | 24.1% ❌ |
| 135 | 6 | 2 | 4 | 33.3% ❌ |
| 247 | 1534 | 1530 | 4 | 99.7% ✅ |
| 251 | 2 | 2 | 0 | 100.0% ✅ |

## Estadístiques per Rolling Code (Nib7)

| Nib7 | Total | Matches | Errors | Precisió |
|------|-------|---------|--------|----------|
| 0x0 | 218 | 218 | 0 | 100.0% ✅ |
| 0x1 | 934 | 784 | 150 | 83.9% ❌ |
| 0x2 | 844 | 786 | 58 | 93.1% ⚠️ |
| 0x8 | 200 | 118 | 82 | 59.0% ❌ |

## Anàlisi d'Errors (290 total)

### Errors per Posició de Nibble

| Posició | Descripció | Errors | % |
|---------|------------|--------|---|
| 11 | Flags | 4 | 1.4% |
| 12 | R1 | 4 | 1.4% |
| 14 | P | 286 | 98.6% |

### Primers 10 Errors Detallats

| # | House | Ch | Temp | Nib7 | Capturada | Generada | Diferències |
|---|-------|----|----|------|-----------|----------|-------------|
| 1 | 3 | 1 | 18.7°C | 0x1 | `ec401301781033b` | `ec401301781033c` | pos14:B→C |
| 2 | 3 | 1 | 18.7°C | 0x1 | `ec401301781033b` | `ec401301781033c` | pos14:B→C |
| 3 | 3 | 1 | 18.7°C | 0x1 | `ec401301781033b` | `ec401301781033c` | pos14:B→C |
| 4 | 3 | 1 | 18.7°C | 0x1 | `ec401301781033b` | `ec401301781033c` | pos14:B→C |
| 5 | 3 | 1 | 23.0°C | 0x1 | `ec401301032082e` | `ec401301032082a` | pos14:E→A |
| 6 | 3 | 1 | 23.0°C | 0x1 | `ec401301032082e` | `ec401301032082a` | pos14:E→A |
| 7 | 3 | 1 | 25.5°C | 0x1 | `ec4013015520f2c` | `ec4013015520f2b` | pos14:C→B |
| 8 | 3 | 1 | 25.5°C | 0x1 | `ec4013015520f2c` | `ec4013015520f2b` | pos14:C→B |
| 9 | 3 | 1 | 26.9°C | 0x1 | `ec401301962043e` | `ec4013019620439` | pos14:E→9 |
| 10 | 3 | 1 | 26.9°C | 0x1 | `ec401301962043e` | `ec4013019620439` | pos14:E→9 |

---

**Generador**: `oregon_optimized_generator.py` amb `oregon_p_lut_complete.py`
**Data**: 2025-11-19 - 2025-11-20
