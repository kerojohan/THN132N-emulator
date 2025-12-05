#!/usr/bin/env python3
"""
Hipòtesi: XOR_Transform depèn del valor M calculat, no de la temperatura.
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def test_m_dependency():
    data = []
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                temp_c = float(row['temperature_C'])
                r12_val = int(row['R12'], 16)
                
                r1 = (r12_val >> 8) & 0xF
                m = (r12_val >> 4) & 0xF
                p = r12_val & 0xF
                
                t_idx = int(round((temp_c + 40) * 10))
                
                data.append({
                    'house': house,
                    'temp_c': temp_c,
                    'temp_idx': t_idx,
                    'r1': r1,
                    'm': m,
                    'p': p
                })
                
            except (ValueError, KeyError):
                continue
                
    # Crear P_Base amb House 3
    base_house = 3
    p_base = {}
    m_base = {}
    
    for d in data:
        if d['house'] == base_house:
            t = d['temp_idx']
            if t not in p_base:
                p_base[t] = d['p']
                m_base[t] = d['m']
                
    print(f"P_Base (House {base_house}): {len(p_base)} punts\n")
    
    # Per House 247, analitzar XOR vs M
    h = 247
    data_h = [d for d in data if d['house'] == h]
    
    xor_by_m = defaultdict(list)
    
    for d in data_h:
        t = d['temp_idx']
        if t in p_base:
            xor_needed = d['p'] ^ p_base[t]
            m_val = d['m']
            
            xor_by_m[m_val].append(xor_needed)
            
    print(f"House {h} - Anàlisi XOR vs M:")
    print("M  | XORs observats")
    print("---|----------------")
    
    for m_val in sorted(xor_by_m.keys()):
        xors = xor_by_m[m_val]
        unique_xors = sorted(set(xors))
        most_common = max(set(xors), key=xors.count)
        count = xors.count(most_common)
        percent = count / len(xors) * 100
        
        print(f"{m_val:2d} | {unique_xors} (mode={most_common}, {percent:.0f}%)")
        
        if len(unique_xors) == 1:
            print(f"   ✨ XOR CONSTANT per M={m_val}: 0x{unique_xors[0]:X}")
            
    # Provar: P(House247) = P_Base(Temp) ^ f(M)
    print("\n\nProvant P = P_Base ^ f(M)...")
    
    # f(M) podria ser: M & Mask, M ^ K, etc.
    for mask in range(16):
        matches = 0
        total = 0
        
        for d in data_h:
            t = d['temp_idx']
            if t in p_base:
                predicted_p = p_base[t] ^ (d['m'] & mask)
                if predicted_p == d['p']:
                    matches += 1
                total += 1
                
        if total > 0:
            score = matches / total
            if score > 0.5:
                print(f"  P = P_Base ^ (M & 0x{mask:X}): {matches}/{total} ({score*100:.1f}%)")

if __name__ == "__main__":
    test_m_dependency()
