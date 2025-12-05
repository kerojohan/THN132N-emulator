#!/usr/bin/env python3
"""
Analitza la correlació entre House Code i nibble 7.
"""

import csv
from pathlib import Path
from collections import defaultdict, Counter

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def analyze_house_vs_nib7():
    house_nib7_map = defaultdict(set)
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                payload_hex = row['payload64_hex']
                
                nibbles = [int(c, 16) for c in payload_hex]
                nib7 = nibbles[7]
                
                house_nib7_map[house].add(nib7)
                
            except (ValueError, KeyError):
                continue
    
    print(f"Correlació House Code vs Nibble 7:\n")
    print(f"House | Nib7 values | House_bin        | Nib7")
    print(f"------|-------------|------------------|------")
    
    for house in sorted(house_nib7_map.keys()):
        nib7_values = sorted(house_nib7_map[house])
        
        if len(nib7_values) == 1:
            nib7 = nib7_values[0]
            house_bin = f"{house:08b}"
            nib7_bin = f"{nib7:04b}"
            nib7_str = str([f'{n:X}' for n in nib7_values])
            print(f"{house:5d} | {nib7_str:11} | {house_bin} | {nib7:X} ({nib7_bin})")
    
    print(f"\nBuscant patró...")
    
    # Provar diferents hipòtesis
    print(f"\nHipòtesis:")
    
    for house in sorted(house_nib7_map.keys()):
        if len(house_nib7_map[house]) > 1:
            continue
        
        nib7 = list(house_nib7_map[house])[0]
        
        # Hipòtesi 1: Nib7 = House & Mask
        for mask in [0xF, 0xF0, 0x0F, 0x3, 0xC]:
            if (house & mask) == nib7 or ((house >> 4) & 0xF) == nib7:
                pass  # No printem tots
        
        # Hipòtesi 2: Nib7 depèn de bits específics
        # Bit 0 de House -> ?
        # Provem totes les combinacions de 4 bits del House
        
    # Millor: Buscar funció
    print(f"\nProvant funcions House -> Nib7:")
    
    test_functions = {
        'House & 0xF': lambda h: h & 0xF,
        '(House >> 4) & 0xF': lambda h: (h >> 4) & 0xF,
        'House & 0x3': lambda h: h & 0x3,
        '(House & 0x8) | (House & 0x2) | (House & 0x1))': lambda h: (h & 0x8) | (h & 0x2) | (h & 0x1),
        'Parell/Senar': lambda h: 0x2 if h % 2 == 1 else 0x8,
    }
    
    for name, func in test_functions.items():
        matches = 0
        total = 0
        
        for house, nib7_set in house_nib7_map.items():
            if len(nib7_set) != 1:
                continue
            
            nib7_real = list(nib7_set)[0]
            nib7_calc = func(house)
            
            if nib7_calc == nib7_real:
                matches += 1
            total += 1
        
        if matches / total > 0.5:
            print(f"  {name:40s}: {matches}/{total} ({matches/total*100:.1f}%)")

if __name__ == "__main__":
    analyze_house_vs_nib7()
