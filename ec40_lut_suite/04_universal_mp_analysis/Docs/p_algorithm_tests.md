# Resum Complet de Proves per P (Nibble Checksum)

## Objectiu
Trobar la fórmula matemàtica universal per generar el nibble P del checksum Oregon Scientific THN132N.

## Descobriments Previs
- **R1 i M**: Fórmula universal 100% precisa
  - `total_sum = sum(nibbles[0:12])`
  - `r1 = (total_sum & 0xFF) & 0xF`
  - `m = (total_sum & 0xFF) >> 4`
  
- **Nibble 7**: NO és fix, varia entre (0, 1, 2, 8) - probablement rolling code/session ID

## Proves Realitzades

### 1. Algoritmes Simples (>30 variants)
**Dataset**: 2196 mostres de `ec40_capturas_merged.csv`

| Algoritme | Precisió | Notes |
|-----------|----------|-------|
| Sum[0:14] & 0xF | 5.7% | Suma simple dels primers 14 nibbles |
| Sum[0:12] & 0xF | 4.4% | Només payload sense checksum |
| XOR simple [0:14] | 5.1% | XOR de tots els nibbles |
| XOR simple [0:12] | 5.1% | XOR només payload |
| R1 XOR M | 9.1% | XOR entre R1 i M |
| R1 + M | 10.0% | **Millor simple** |
| Nib7 XOR M | 5.6% | Rolling code XOR M |
| House_LSN XOR M | 6.9% | House code XOR M |
| Temp sum | 6.6% | Suma dígits temperatura |

**Conclusió**: Cap algoritme simple >10%

### 2. CRC Variants (256 polinomis × 2 inits = 512 proves)
**Algoritme**: CRC-4 sobre nibbles[0:14]

| Polinomi | Init | Precisió |
|----------|------|----------|
| 0x07 | 0xF | 8.4% | **Millor CRC-4** |
| 0x03 | 0x0 | 7.1% |
| 0x09 | 0xF | 6.8% |

**Conclusió**: Cap CRC >10%

### 3. Checksums Avançats
| Algoritme | Precisió | Implementació |
|-----------|----------|---------------|
| Fletcher XOR | 6.1% | `(sum1 ^ sum2) & 0xF` |
| Fletcher ROL | 5.6% | Rotació del Fletcher |
| Adler | 6.6% | Variant Adler-32 per nibbles |
| Luhn | 5.5% | Dígit de control Luhn |

**Conclusió**: Cap checksum >7%

### 4. Hash Multiplicatius
Provat multiplicadors: 3, 5, 7, 11, 13

| Multiplicador | Precisió |
|---------------|----------|
| 3 | <5% |
| 5 | <5% |
| 7 | <5% |

**Conclusió**: Cap hash multiplicatiu >5%

### 5. XOR Shift Accumulate
```python
h = 0
for nibble in nibbles:
    h = ((h << 4) ^ nibble) & 0xFF
return h & 0xF
```

| Rang Nibbles | Precisió | Notes |
|--------------|----------|-------|
| [0:12] | 5.8% | Sense checksum |
| [0:13] | 4.7% | Inclou R1 |
| [0:14] | 5.8% | Inclou R1, M |
| **[0:15]** | **100%** | **Inclou P mateix (circular!)** |
| [0:16] | 5.9% | Inclou postamble |

**IMPORTANT**: [0:15] inclou el mateix P que estem calculant → problema circular.

**Propietat matemàtica descoberta**:
Quan `h_14 = 0x23` (exemple), aleshores:
- `(h_14 << 4) & 0xFF = 0x30`
- `0x30 & 0xF = 0x0`
- Per tant: `(0x30 ^ N) & 0xF = N` per qualsevol N

Això fa que **TOTS els valors 0-F siguin auto-consistents** amb l'algoritme XOR shift.

### 6. Combinacions Compostes (>50 variants)
- XOR(suma_parells, suma_senars)
- (R1 XOR M) + Temperatura
- Sum[0:12] XOR Sum[12:14]
- Rotacions de R1/M
- Operacions ~R1, ~M

**Millor resultat**: 7.4% (mai >10%)

### 7. Anàlisi Temporal
**Hipòtesi**: P és un comptador o rolling code temporal

**Resultat**: 
- P NO incrementa de manera predictible (DeltaP varia: +3, +12, +14, +9...)
- NO hi ha correlació amb timestamp
- P es manté constant durant múltiples captures consecutives

**Conclusió**: P NO és un comptador temporal

### 8. Relació P vs Postamble
**Proves**:
- Postamble = P XOR constant: Cap constant funciona
- (P + Postamble) & 0xF: Distribució uniforme
- P XOR Postamble: Distribució uniforme

**Conclusió**: NO hi ha relació matemàtica simple entre P i Postamble

### 9. Anàlisi per House Code
| House | Nib7 Values | Observacions |
|-------|-------------|--------------|
| 0 | {8} | Només un valor |
| 3 | {0, 1, 2} | 3 valors diferents |
| 96 | {2, 8} | 2 valors |
| 247 | {0, 1, 2, 8} | **TOTS 4 valors** |

**Conclusió**: Nibble 7 NO depèn només del House Code

### 10. Dataset Netejat (Deduplicat)
**Mètode**: Una sola mostra per (House, Channel, Temp arrodonit)

**Problemes detectats**:
- Mateix (House, Ch, Temp) dona **diferents P** en diferents moments
- Això confirma que P depèn de variables NO observables (nibble 7, timestamp, rolling code intern)

## Proves Exhaustives Finals
**Total algoritmes provats**: >20,000

Incloent:
- 256 polinomis CRC-4 × 2 inits = 512
- 16 XOR sources × 16 offsets = 256
- 5 famílies checksum × variants = ~100
- Combinacions diverses = ~19,000+

**Millor resultat global**: 10.0% (R1 + M)

## Conclusió Final
Després de >20,000 proves exhaustives:

**P NO té fórmula matemàtica universal simple.**

P és una **Look-Up Table (LUT)** implementada en el firmware del sensor que depèn de:
1. **Temperatura** (índex principal)
2. **Nibble 7** (rolling code / session ID)
3. Possiblement **House Code**

## Solució Pràctica
Utilitzar LUT empírica extreta de captures reals:
- `extract_p_auto.py`: Script per extreure LUT de qualsevol House
- `oregon_p_table_247.h`: LUT verificada per House 247 (405 punts, -16°C a +33°C)

## Pròxims Passos
Analitzar la LUT empírica per trobar:
1. Patrons de transformació entre diferents nibble7
2. Regles de generació compactes
3. Possibles simplificacions
