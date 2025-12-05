#!/usr/bin/env python3
"""
GENERADOR FINAL OPTIMITZAT amb LUT Base + Transformació XOR.
Només necessita una LUT per Nib7=2 (la més completa) i aplica XOR per altres nib7.
"""

import csv
from pathlib import Path

# Taula de transformació XOR (base: Nib7=2)
# P(nib7_target) = P(nib7_base=2) XOR NIB7_XOR_TABLE[nib7_target]
NIB7_XOR_TABLE = {
    0x0: 0x6,  # P(0) = P(2) XOR 0x6
    0x1: 0xD,  # P(1) = P(2) XOR 0xD
    0x2: 0x0,  # P(2) = P(2) XOR 0x0 (base)
    0x8: 0x7,  # P(8) = P(2) XOR 0x7
}

# LUT Base per Nib7=2 (House 247)
# Extreta de captures reals
# Índex: temp_idx = int((temp_c + 40) * 10)
P_LUT_BASE = {}

def load_p_lut_base():
    """Carrega la LUT base des de les captures."""
    global P_LUT_BASE
    
    BASE_DIR = Path(__file__).parent.parent
    DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                if house != 247:
                    continue
                
                temp_c = float(row['temperature_C'])
                payload_hex = row['payload64_hex']
                
                nibbles = [int(c, 16) for c in payload_hex]
                nib7 = nibbles[7]
                p = nibbles[14]
                
                # Només Nib7=2 per la LUT base
                if nib7 != 0x2:
                    continue
                
                temp_idx = int(round((temp_c + 40) * 10))
                
                if temp_idx not in P_LUT_BASE:
                    P_LUT_BASE[temp_idx] = p
                    
            except (ValueError, KeyError):
                continue
    
    print(f"LUT Base carregada: {len(P_LUT_BASE)} punts")
    print(f"Rang: {(min(P_LUT_BASE.keys())-400)/10:.1f}°C - {(max(P_LUT_BASE.keys())-400)/10:.1f}°C")

def calculate_p(temp_celsius, nib7):
    """
    Calcula P utilitzant LUT base +transformació XOR.
    
    Args:
        temp_celsius: Temperatura en °C
        nib7: Rolling code (0, 1, 2, o 8)
        
    Returns:
        P nibble (0-F)
    """
    # Índex temperatura
    temp_idx = int(round((temp_celsius + 40) * 10))
    
    # Obtenir P base (per Nib7=2)
    if temp_idx not in P_LUT_BASE:
        # Temperatura fora de rang - usar el més proper
        closest_idx = min(P_LUT_BASE.keys(), key=lambda k: abs(k - temp_idx))
        p_base = P_LUT_BASE[closest_idx]
    else:
        p_base = P_LUT_BASE[temp_idx]
    
    # Aplicar transformació XOR
    xor_val = NIB7_XOR_TABLE.get(nib7, 0x0)
    p = p_base ^ xor_val
    
    return p & 0xF

def generate_frame(house_id, channel, temp_celsius, rolling_code=0x2):
    """Genera trama completa de 15 nibbles."""
    nibbles = []
    
    # 1. ID (EC40)
    nibbles.extend([0xE, 0xC, 0x4, 0x0])
    
    # 2. Channel
    nibbles.append(channel & 0xF)
    
    # 3. House
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
    
    # 7. R1, M (checksum senzill)
    total_sum = sum(nibbles)
    checksum_byte = total_sum & 0xFF
    r1 = checksum_byte & 0xF
    m = (checksum_byte >> 4) & 0xF
    nibbles.extend([r1, m])
    
    # 8. P (LUT + XOR transform)
    p = calculate_p(temp_celsius, rolling_code)
    nibbles.append(p)
    
    return ''.join(f'{n:x}' for n in nibbles)

def verify_generator():
    """Verifica el generador contra TOTES les captures."""
    
    BASE_DIR = Path(__file__).parent.parent
    DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"
    
    matches = 0
    total = 0
    errors_by_nib7 = {0: 0, 1: 0, 2: 0, 8: 0}
    total_by_nib7 = {0: 0, 1: 0, 2: 0, 8: 0}
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                channel = int(row['channel'])
                temp_c = float(row['temperature_C'])
                captured = row['payload64_hex']
                
                nibbles_captured = [int(c, 16) for c in captured]
                nib7 = nibbles_captured[7]
                
                # Generar
                generated = generate_frame(house, channel, temp_c, nib7)
                
                # Comparar (15 nibbles)
                captured_15 = captured[:15]
                
                total += 1
                if nib7 in total_by_nib7:
                    total_by_nib7[nib7] += 1
                
                if generated == captured_15:
                    matches += 1
                else:
                    if nib7 in errors_by_nib7:
                        errors_by_nib7[nib7] += 1
                        
            except (ValueError, KeyError):
                continue
    
    print(f"\n{'='*70}")
    print("VERIFICACIÓ COMPLETA")
    print(f"{'='*70}")
    print(f"\nTotal: {total} trames")
    print(f"Matches: {matches} ({matches/total*100:.2f}%)")
    print(f"Errors: {total-matches}")
    
    print(f"\nPer Nib7:")
    for nib7 in sorted(total_by_nib7.keys()):
        if total_by_nib7[nib7] > 0:
            errors = errors_by_nib7[nib7]
            success = total_by_nib7[nib7] - errors
            pct = success / total_by_nib7[nib7] * 100
            status = "✅" if pct > 99 else "⚠️" if pct > 90 else "❌"
            print(f"  {status} Nib7={nib7:X}: {success}/{total_by_nib7[nib7]} ({pct:.1f}%)")

if __name__ == "__main__":
    print("Carregant LUT base...")
    load_p_lut_base()
    
    print(f"\nTaula de transformació XOR:")
    for nib7, xor_val in sorted(NIB7_XOR_TABLE.items()):
        print(f"  Nib7={nib7:X}: XOR 0x{xor_val:X}")
    
    # Verificar
    verify_generator()
