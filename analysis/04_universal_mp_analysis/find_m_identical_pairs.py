#!/usr/bin/env python3
"""
Busca altres parells de house codes que puguin tenir taula M idèntica
basant-se en el patró descobert: XOR nibble baix = 0x4
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent

def load_house_codes():
    """Carrega tots els house codes disponibles"""
    CSV_FILES = [
        BASE_DIR / "ec40_live.csv",
        BASE_DIR / "ec40_live_1.csv", 
        BASE_DIR / "ec40_capturas_merged.csv"
    ]
    
    house_codes = set()
    for csv_file in CSV_FILES:
        if not csv_file.exists():
            continue
        with open(csv_file, 'r') as f:
            for row in csv.DictReader(f):
                try:
                    house_codes.add(int(row['house_code']))
                except (ValueError, KeyError):
                    continue
    
    return sorted(house_codes)

print("="*70)
print("CERCA DE PARELLS AMB PATRÓ M IDÈNTIC")
print("="*70)

house_codes = load_house_codes()
print(f"\nHouse codes disponibles: {house_codes}")

# Buscar parells amb XOR nibble baix = 0x4
pattern_matches = []

print("\n" + "="*70)
print("PARELLS AMB (H1 XOR H2) & 0x0F == 0x4")
print("="*70)

for i, h1 in enumerate(house_codes):
    for h2 in house_codes[i+1:]:
        xor = h1 ^ h2
        nibble_baix = xor & 0x0F
        
        if nibble_baix == 0x4:
            pattern_matches.append((h1, h2, xor))
            print(f"\n✅ House {h1:3d} (0x{h1:02X}) vs House {h2:3d} (0x{h2:02X})")
            print(f"   House XOR = 0x{xor:02X} = 0b{xor:08b}")
            print(f"   Nibble baix = 0x{nibble_baix:X} ✓")

print(f"\n{'='*70}")
print(f"TOTAL PARELLS TROBATS: {len(pattern_matches)}")
print(f"{'='*70}")

# Analitzar el nibble baix de cada house code
print("\n" + "="*70)
print("ANÀLISI DELS BITS BAIXOS (nibble baix) DE CADA HOUSE CODE")
print("="*70)

by_nibble = defaultdict(list)
for hc in house_codes:
    nibble = hc & 0x0F
    by_nibble[nibble].append(hc)

print("\nHouse codes agrupats per nibble baix:")
for nibble in sorted(by_nibble.keys()):
    houses = by_nibble[nibble]
    print(f"\n  Nibble 0x{nibble:X}: {houses}")
    if len(houses) > 1:
        print(f"    → Si la hipòtesi és correcta, tots aquests comparteixen taula M!")

# Hipòtesi refinada
print("\n" + "="*70)
print("HIPÒTESI REFINADA")
print("="*70)
print("\n1. PATRÓ XOR DETECTAT:")
print("   Si (house1 XOR house2) & 0x0F == 0x4, llavors M_table[house1] == M_table[house2]")

print("\n2. INTERPRETACIÓ ALTERNATIVA:")
print("   Possiblement la taula M està determinada pels 4 bits baixos del house code")
print("   És a dir: M_table depèn de (house_code & 0x0F)")

print("\n3. PREDICCIONS BASADES EN AQUESTA HIPÒTESI:")
for nibble in sorted(by_nibble.keys()):
    if len(by_nibble[nibble]) > 1:
        houses = by_nibble[nibble]
        print(f"   - Houses {houses} haurien de tenir taula M idèntica")

print("\n4. VALIDACIÓ NECESSÀRIA:")
print("   Cal verificar si TOTS els house codes amb el mateix nibble baix")
print("   tenen realment la mateixa taula M, no només els que difereixen en 0x4")

print("\n" + "="*70)
print("PROPERA ACCIÓ RECOMANADA")
print("="*70)
print("\nModificar l'script analyze_overlapping_pairs.py per comprovar:")
print("1. Tots els parells amb XOR nibble baix = 0x4")
print("2. Tots els parells amb el mateix nibble baix (house1 & 0xF == house2 & 0xF)")
print("3. Verificar si la taula M només depèn dels 4 bits baixos del house code")
