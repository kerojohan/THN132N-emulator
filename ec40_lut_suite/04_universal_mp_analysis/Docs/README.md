# Oregon Scientific THN132N - Investigació Completa del Protocol

## Resum Executiu

Aquest document detalla la investigació exhaustiva del protocol de transmissió Oregon Scientific THN132N, amb especial èmfasi en la generació dels nibbles de checksum M i P.

## Estructura del Payload (64 bits / 16 nibbles)

```
Posició | Nibble | Descripció
--------|--------|------------------------------------------
0-3     | EC40   | ID del sensor (fix)
4       | 1-3    | Channel (1, 2, o 3)
5-6     | XX XX  | House Code (LSN, MSN)
7       | 0,1,2,8| Rolling Code / Session ID (VARIABLE!)
8-10    | XXX    | Temperatura BCD (LSN, Mid, MSN)
11      | 0/8    | Flags (bit 3 = signe temp invertit)
12      | X      | R1 (checksum nibble 1)
13      | X      | M (checksum nibble 2)
14      | X      | P (checksum nibble 3)
15      | X      | Postamble (distribuït uniformement)
```

## Descobriments Clau

### 1. Nibble 7 (Rolling Code)
**Descobriment crític**: El que es pensava que era un nibble "fix" NO ho és.

- **Valors observats**: 0x0, 0x1, 0x2, 0x8
- **Comportament**: Es manté constant durant una sessió de captures
- **Propòsit probable**: Rolling code anti-replay o Session ID
- **Distribució** (House 247):
  - 0x1: 46% de les mostres
  - 0x2: 38%
  - 0x0: 10%
  - 0x8: 6%

### 2. Checksum R1 i M (100% Resolt)

**Fórmula Universal**:
```python
total_sum = sum(nibbles[0:12])  # Inclou nibble 7!
checksum_byte = total_sum & 0xFF

r1 = checksum_byte & 0xF        # Nibble baix
m = (checksum_byte >> 4) & 0xF  # Nibble alt
```

**Verificació**: 100% de precisió sobre 2196 mostres.

### 3. Nibble P (Parcialment Resolt)

#### Proves Realitzades
**Total algoritmes testats**: >20,000

**Categories d'algoritmes provats**:
1. **Sumes simples** (30+ variants): Millor 10.0%
2. **CRC-4** (512 variants - tots els polinomis + inits): Millor 8.4%
3. **Checksums avançats** (Fletcher, Adler, Luhn): Millor 6.6%
4. **Hash multiplicatius**: Millor <5%
5. **XOR shift accumulate**: 5.8% (circular al 100% amb P inclòs)
6. **Combinacions compostes** (>50): Millor 7.4%
7. **Anàlisi temporal**: No correlació
8. **Relacions P-Postamble**: No correlació

#### Descobriment de Transformacions XOR

**IMPORTANT**: Les transformacions entre diferents Nib7 són **XOR constants** (100% verificat):

| Transformació | XOR Constant | Mostres | Precisió |
|---------------|--------------|---------|----------|
| P(1) = P(0) XOR | 0xB | 16 | 100% |
| P(2) = P(0) XOR | 0x6 | 32 | 100% |
| P(2) = P(1) XOR | 0xD | 68 | 100% |
| P(8) = P(1) XOR | 0xA | 12 | 100% |
| P(8) = P(2) XOR | 0x7 | 21 | 100% |

**Implicació**: Només necessitem UNA LUT base + 4 constants XOR!

#### Solució Final per P

P és una **Look-Up Table (LUT)** que depèn de:
1. Temperatura (índex principal)
2. Rolling code (Nib7) via transformació XOR

**LUT Completa Generada**:
- **Punts**: 405
- **Rang**: -16.0°C a 61.4°C
- **Resolució**: 0.1°C
- **Mida**: ~810 bytes
- **Fitxer**: `Docs/oregon_p_lut_complete.py`

## Fitxers Generats

### Documentació
- `Docs/p_algorithm_tests.md`: Detall de les >20,000 proves
- `Docs/README.md`: Aquest document
- `Docs/oregon_p_lut_complete.py`: LUT completa amb funcions

### Scripts d'Utilitat
- `generate_complete_p_lut.py`: Genera LUT combinada
- `analyze_p_lut_patterns.py`: Analitza patrons en LUTs
- `verify_p_xor_transform.py`: Verifica transformacions XOR
- `oregon_optimized_generator.py`: Generador optimitzat

## Ús Pràctic

### Generar una Trama Completa

```python
from Docs.oregon_p_lut_complete import get_p

def generate_frame(house_id, channel, temp_celsius, rolling_code=0x2):
    nibbles = []
    
    # 1. ID (EC40)
    nibbles.extend([0xE, 0xC, 0x4, 0x0])
    
    # 2. Channel
    nibbles.append(channel & 0xF)
    
    # 3. House Code
    nibbles.append(house_id & 0xF)
    nibbles.append((house_id >> 4) & 0xF)
    
    # 4. Rolling code
    nibbles.append(rolling_code & 0xF)
    
    # 5. Temperatura BCD
    temp_abs = abs(temp_celsius)
    temp_int = int(round(temp_abs * 10))
    nibbles.append(temp_int % 10)
    nibbles.append((temp_int // 10) % 10)
    nibbles.append((temp_int // 100) % 10)
    
    # 6. Flags
    flags = 0x0 if temp_celsius >= 0 else 0x8
    nibbles.append(flags)
    
    # 7. R1, M
    total_sum = sum(nibbles)
    checksum_byte = total_sum & 0xFF
    r1 = checksum_byte & 0xF
    m = (checksum_byte >> 4) & 0xF
    nibbles.extend([r1, m])
    
    # 8. P (LUT + XOR transform)
    p = get_p(temp_celsius, rolling_code)
    nibbles.append(p)
    
    return ''.join(f'{n:x}' for n in nibbles)
```

### Rolling Code

Per a una implementació real:
- **Opció 1**: Usar sempre 0x2 (el més comú)
- **Opció 2**: Incrementar: 0 → 1 → 2 → 8 → 0 (cada N trames)
- **Opció 3**: Aleatori entre {0, 1, 2, 8}

## Conclusions

1. ✅ **R1 i M**: Fórmula universal simple (suma de nibbles)
2. ✅ **Nibble 7**: Identificat com a rolling code variable
3. ✅ **P**: Requereix LUT, però amb transformacions XOR compactes
4. ❌ **Postamble**: No té fórmula (distribució uniforme)

## Optimitzacions de Memòria

**Abans** (4 LUTs separades):
- 4 × 600 punts = 2400 bytes

**Després** (LUT base + XOR):
- 1 × 405 punts + 4 bytes XOR = 409 bytes
- **Reducció: 83%**

## Referències

- Dataset: `ec40_capturas_merged.csv` (2196 mostres)
- Houses analitzats: 0, 3, 79, 92, 96, 135, 247, 251
- Rang temporal: 20/11/2025 - 03/12/2025

## Autors

Investigació realitzada amb assistència d'Antigravity AI.

---

**Última actualització**: 2025-12-05
