#!/usr/bin/env python3
"""
Verifica la hipòtesi que la taula M depèn del nibble baix del house code.
Comprova:
1. Parells amb XOR nibble baix = 0x4 (el patró original)
2. Parells amb XOR nibble baix = 0x0 (mateix nibble baix)
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent

def load_data():
    """Carrega dades i les organitza per house code"""
    CSV_FILES = [
        BASE_DIR / "ec40_live.csv",
        BASE_DIR / "ec40_live_1.csv", 
        BASE_DIR / "ec40_capturas_merged.csv"
    ]
    
    data_by_house = defaultdict(dict)
    
    for csv_file in CSV_FILES:
        if not csv_file.exists():
            continue
        with open(csv_file, 'r') as f:
            for row in csv.DictReader(f):
                try:
                    house = int(row['house_code'])
                    temp = float(row['temp'])
                    
                    # Extreure M
                    checksum_str = row.get('checksum_hex', row.get('R12', ''))
                    r12 = int(checksum_str, 16) if isinstance(checksum_str, str) else int(checksum_str)
                    m = (r12 >> 4) & 0xF
                    
                    # Guardar (preferim dades més recents si hi ha duplicats, però aquí només guardem un)
                    if temp not in data_by_house[house]:
                        data_by_house[house][temp] = m
                        
                except (ValueError, KeyError, TypeError):
                    continue
    
    return data_by_house

def check_pair(h1, h2, data, expected_xor_m=0):
    """Comprova si dos house codes tenen la mateixa taula M (o XOR constant)"""
    d1 = data.get(h1, {})
    d2 = data.get(h2, {})
    
    common_temps = sorted(set(d1.keys()) & set(d2.keys()))
    
    if len(common_temps) < 3: # Mínim 3 punts per dir alguna cosa
        return None
        
    m_xors = []
    for t in common_temps:
        m_xors.append(d1[t] ^ d2[t])
    
    unique_xors = sorted(set(m_xors))
    
    return {
        'overlap': len(common_temps),
        'unique_xors': unique_xors,
        'consistent': len(unique_xors) == 1 and unique_xors[0] == expected_xor_m
    }

def main():
    print("="*70)
    print("VERIFICACIÓ D'HIPÒTESI: M depèn del nibble baix")
    print("="*70)
    
    data = load_data()
    house_codes = sorted(data.keys())
    print(f"House codes amb dades: {house_codes}\n")
    
    # 1. Comprovar parells amb XOR nibble baix = 0x4
    print("TEST 1: Parells amb (H1 ^ H2) & 0xF == 0x4")
    print("Hipòtesi: Haurien de tenir M XOR = 0 (Taula M idèntica)")
    print("-" * 60)
    
    matches_hypothesis = 0
    total_checked = 0
    
    for i, h1 in enumerate(house_codes):
        for h2 in house_codes[i+1:]:
            if ((h1 ^ h2) & 0xF) == 0x4:
                res = check_pair(h1, h2, data, expected_xor_m=0)
                if res:
                    total_checked += 1
                    status = "✅ CONFIRMAT" if res['consistent'] else f"❌ FALLA (XORs: {res['unique_xors']})"
                    print(f"House {h1:3d} (0x{h1:02X}) vs {h2:3d} (0x{h2:02X}) | Overlap: {res['overlap']:3d} | {status}")
                    if res['consistent']:
                        matches_hypothesis += 1
    
    if total_checked > 0:
        print(f"\nResultat Test 1: {matches_hypothesis}/{total_checked} confirmen la hipòtesi ({matches_hypothesis/total_checked*100:.1f}%)")
    else:
        print("\nCap parell amb prou dades per verificar.")

    # 2. Comprovar parells amb XOR nibble baix = 0x0 (Mateix nibble)
    print("\n" + "="*70)
    print("TEST 2: Parells amb (H1 ^ H2) & 0xF == 0x0 (Mateix nibble baix)")
    print("Hipòtesi: Haurien de tenir M XOR = 0 (Taula M idèntica)")
    print("-" * 60)
    
    matches_hypothesis_2 = 0
    total_checked_2 = 0
    
    for i, h1 in enumerate(house_codes):
        for h2 in house_codes[i+1:]:
            if ((h1 ^ h2) & 0xF) == 0x0:
                res = check_pair(h1, h2, data, expected_xor_m=0)
                if res:
                    total_checked_2 += 1
                    status = "✅ CONFIRMAT" if res['consistent'] else f"❌ FALLA (XORs: {res['unique_xors']})"
                    print(f"House {h1:3d} (0x{h1:02X}) vs {h2:3d} (0x{h2:02X}) | Overlap: {res['overlap']:3d} | {status}")
                    if res['consistent']:
                        matches_hypothesis_2 += 1

    if total_checked_2 > 0:
        print(f"\nResultat Test 2: {matches_hypothesis_2}/{total_checked_2} confirmen la hipòtesi ({matches_hypothesis_2/total_checked_2*100:.1f}%)")
    else:
        print("\nCap parell amb prou dades per verificar.")

    # Conclusions
    print("\n" + "="*70)
    print("CONCLUSIONS")
    print("="*70)
    
    if matches_hypothesis > 0 or matches_hypothesis_2 > 0:
        print("La hipòtesi sembla sòlida: El nibble baix del house code determina la taula M.")
        print("Això explicaria per què House 3 (0x03) i House 247 (0xF7) tenen diferència 0x4 en nibble baix")
        print("i per què House 95 (0x5F) i House 187 (0xBB) tenen diferència 0x4 en nibble baix.")
        print("\nNota: Sembla que els nibbles que difereixen en 0x4 estan relacionats.")
        print("      0x3 XOR 0x7 = 0x4")
        print("      0xF XOR 0xB = 0x4")
    else:
        print("No s'ha pogut confirmar la hipòtesi amb les dades actuals.")

if __name__ == "__main__":
    main()
