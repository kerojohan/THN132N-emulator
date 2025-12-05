#!/usr/bin/env python3
"""
Debug detallat del càlcul de P - comparació nibble a nibble.
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def calculate_p_from_15_nibbles(nibbles_15):
    """Calcula P a partir dels primers 15 nibbles."""
    h = 0
    for nibble in nibbles_15:
        h = ((h << 4) ^ nibble) & 0xFF
    return h & 0xF

# Agafem el primer exemple que falla
with open(DATA_FILE, 'r') as f:
    reader = csv.DictReader(f)
    row = next(reader)
    
    house = int(row['house'])
    channel = int(row['channel'])
    temp_c = float(row['temperature_C'])
    payload_hex = row['payload64_hex']
    
    print(f"EXEMPLE: House {house}, Ch {channel}, Temp {temp_c}°C")
    print(f"Payload captura: {payload_hex}\n")
    
    # Nibbles de la captura
    captured_nibbles = [int(c, 16) for c in payload_hex]
    print(f"Nibbles capturats: {[f'{n:X}' for n in captured_nibbles]}")
    print(f"  Posicions:       {list(range(16))}\n")
    
    # El que genero
    generated_nibbles = []
    
    # 1-4: ID (EC40)
    generated_nibbles.extend([0xE, 0xC, 0x4, 0x0])
    
    # 5: Channel
    generated_nibbles.append(channel & 0xF)
    
    # 6-7: House
    generated_nibbles.append(house & 0xF)
    generated_nibbles.append((house >> 4) & 0xF)
    
    # 8: Fixed
    generated_nibbles.append(0x2)
    
    # 9-11: Temp
    temp_abs = abs(temp_c)
    temp_int = int(round(temp_abs * 10))
    generated_nibbles.append(temp_int % 10)
    generated_nibbles.append((temp_int // 10) % 10)
    generated_nibbles.append((temp_int // 100) % 10)
    
    # 12: Flags
    flags = 0x0 if temp_c >= 0 else 0x8
    generated_nibbles.append(flags)
    
    print(f"Nibbles generats (0-11): {[f'{n:X}' for n in generated_nibbles]}")
    print(f"Nibbles capturats (0-11): {[f'{n:X}' for n in captured_nibbles[:12]]}")
    
    match = "✓" if generated_nibbles == captured_nibbles[:12] else "✗"
    print(f"{match} Els primers 12 nibbles coincideixen\n")
    
    # Càlcul checksum
    total_sum = sum(generated_nibbles)
    checksum_byte = total_sum & 0xFF
    r1 = checksum_byte & 0xF
    m = (checksum_byte >> 4) & 0xF
    
    print(f"Checksum R1, M:")
    print(f"  Generat:  R1={r1:X}, M={m:X}")
    print(f"  Capturat: R1={captured_nibbles[12]:X}, M={captured_nibbles[13]:X}")
    
    match_r1 = "✓" if r1 == captured_nibbles[12] else "✗"
    match_m = "✓" if m == captured_nibbles[13] else "✗"
    print(f"  {match_r1} R1, {match_m} M\n")
    
    # Afegir R1, M als generats
    generated_nibbles.extend([r1, m])
    
    # Ara calcular P sobre els 14 nibbles que tenim
    print(f"Càlcul de P:")
    print(f"  Nibbles per P (generats 0-13): {[f'{n:X}' for n in generated_nibbles]}")
    print(f"  Nibbles per P (capturats 0-13): {[f'{n:X}' for n in captured_nibbles[:14]]}")
    
    p_generated = calculate_p_from_15_nibbles(generated_nibbles)
    p_from_captured_14 = calculate_p_from_15_nibbles(captured_nibbles[:14])
    p_from_captured_15 = calculate_p_from_15_nibbles(captured_nibbles[:15])
    p_real = captured_nibbles[14]
    
    print(f"\n  P generat (sobre 14 generats):      {p_generated:X}")
    print(f"  P calculat (sobre 14 capturats):    {p_from_captured_14:X}")
    print(f"  P calculat (sobre 15 capturats):    {p_from_captured_15:X}")
    print(f"  P real (captura pos 14):            {p_real:X}")
    
    if p_from_captured_15 == p_real:
        print(f"\n✓ P es calcula sobre els primers 15 nibbles!")
    else:
        print(f"\n✗ Alguna cosa no quadra...")

if __name__ == "__main__":
    pass
