#!/usr/bin/env python3
"""
Extreu i compara les 8 Taules M Base (LUTs).
Agrupa per Key = House & 0x0B.
Genera una visualització per comparar-les.
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "04_universal_mp_analysis" / "golden_master.csv"

def load_luts():
    groups = defaultdict(lambda: defaultdict(list))
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            h = int(row['house'])
            t = int(row['temp_idx'])
            m = int(row['m'])
            
            key = h & 0x0B
            groups[key][t].append(m)
            
    # Consolidar LUTs (moda)
    luts = {}
    for key, t_map in groups.items():
        lut = {}
        for t, ms in t_map.items():
            most_common = max(set(ms), key=ms.count)
            lut[t] = most_common
        luts[key] = lut
        
    return luts

def main():
    print("="*70)
    print("COMPARACIÓ DE LES 8 TAULES M BASE")
    print("="*70)
    
    luts = load_luts()
    all_keys = sorted(luts.keys())
    
    # Trobar rang de T comú per visualitzar
    min_t = 9999
    max_t = -9999
    for lut in luts.values():
        if not lut: continue
        min_t = min(min_t, min(lut.keys()))
        max_t = max(max_t, max(lut.keys()))
        
    print(f"Rang T: {min_t} a {max_t}")
    print(f"Keys trobades: {[hex(k) for k in all_keys]}")
    
    # Visualitzar costat a costat
    print("\nTemp  | " + " | ".join([f"K={k:X}" for k in all_keys]))
    print("-" * (8 + 6 * len(all_keys)))
    
    # Mostrem cada 5 punts per no fer-ho etern
    for t in range(min_t, max_t + 1):
        # Només mostrem si almenys una taula té dades
        has_data = any(t in luts[k] for k in all_keys)
        if not has_data:
            continue
            
        row = f"{t:4d}  |"
        for k in all_keys:
            val = luts[k].get(t, ".")
            row += f"  {val}  |"
        print(row)

    # Anàlisi de diferències (XOR) entre taules
    print("\n" + "="*70)
    print("ANÀLISI DE DIFERÈNCIES (XOR) ENTRE GRUPS")
    print("="*70)
    
    # Prenem K=0x8 com a referència (té moltes dades)
    ref_key = 0x8
    if ref_key not in luts:
        ref_key = all_keys[0]
        
    print(f"Referència: K=0x{ref_key:X}")
    
    for k in all_keys:
        if k == ref_key: continue
        
        # Calcular XOR amb referència
        xors = []
        common_pts = 0
        
        for t, m in luts[k].items():
            if t in luts[ref_key]:
                xors.append(m ^ luts[ref_key][t])
                common_pts += 1
        
        unique_xors = sorted(set(xors))
        print(f"K=0x{k:X} vs Ref(0x{ref_key:X}): {common_pts} pts comuns. XORs: {unique_xors}")
        
        if len(unique_xors) == 1:
            print(f"  ✅ XOR CONSTANT: 0x{unique_xors[0]:X}")
            print(f"  Implica: M(K) = M(Ref) ^ 0x{unique_xors[0]:X}")

if __name__ == "__main__":
    main()
