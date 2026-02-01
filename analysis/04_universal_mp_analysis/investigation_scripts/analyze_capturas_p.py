#!/usr/bin/env python3
"""
Analitza P utilitzant ec40_capturas_merged.csv directament.
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def analyze_p_from_capturas():
    print(f"Analitzant {DATA_FILE}...")
    
    # House -> {TempIdx -> P}
    p_luts = defaultdict(dict)
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                temp_c = float(row['temperature_C'])
                r12_str = row['R12']
                
                # R12 és 0x8AA -> 8, A, A
                # R1=8, M=A, P=A
                r12_val = int(r12_str, 16)
                
                r1 = (r12_val >> 8) & 0xF
                m = (r12_val >> 4) & 0xF
                p = r12_val & 0xF
                
                # TempIdx
                t_idx = int(round((temp_c + 40) * 10))
                
                p_luts[house][t_idx] = p
                
            except (ValueError, KeyError):
                continue
                
    print(f"Houses trobades: {sorted(p_luts.keys())}")
    for h in sorted(p_luts.keys()):
        print(f"  House {h} (0x{h:X}): {len(p_luts[h])} punts")
        
    # Comparar P entre houses
    if 247 in p_luts:
        print(f"\n✅ House 247 present amb {len(p_luts[247])} punts!")
        
        # Mostrar mostra
        temps = sorted(p_luts[247].keys())[:10]
        print("Mostra House 247:")
        for t in temps:
            temp_c = (t / 10.0) - 40.0
            print(f"  T={temp_c:5.1f}°C -> P=0x{p_luts[247][t]:X}")

if __name__ == "__main__":
    analyze_p_from_capturas()
