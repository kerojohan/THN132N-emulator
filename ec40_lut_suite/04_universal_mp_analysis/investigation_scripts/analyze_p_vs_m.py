#!/usr/bin/env python3
"""
Hipòtesi Final: P depèn del valor M calculat + House bits.
P = f(M, House, TempDecimal)
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "04_universal_mp_analysis" / "golden_master.csv"

def get_nibbles(hex_str):
    return [int(c, 16) for c in hex_str]

def load_data_with_m():
    """Carrega dades incloent M calculat."""
    data = []
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            h = int(row['house'])
            t_idx = int(row['temp_idx'])
            m = int(row['m'])
            p = int(row['p'])
            
            # Temperatura
            temp_c = (t_idx / 10.0) - 40.0
            t_dec = int(round(abs(temp_c) * 10)) % 10
            
            data.append({
                'house': h,
                'temp_idx': t_idx,
                'temp_dec': t_dec,
                'm': m,
                'p': p
            })
            
    return data

def analyze_p_vs_m():
    data = load_data_with_m()
    print(f"Analitzant {len(data)} registres...")
    
    # Provar: P = M ^ (House & Mask) ^ (TempDec & Mask2)
    print("\nProvant P = M ^ (House & MaskH) ^ (TempDec & MaskT)...")
    
    best_score = 0
    best_masks = None
    
    for mask_h in range(16): # House pot ser 0-255, però provem nibble baix
        for mask_t in range(16): # TempDec 0-9
            matches = 0
            
            for d in data:
                h_contrib = (d['house'] & mask_h) & 0xF
                t_contrib = (d['temp_dec'] & mask_t) & 0xF
                
                pred_p = (d['m'] ^ h_contrib ^ t_contrib) & 0xF
                
                if pred_p == d['p']:
                    matches += 1
                    
            score = matches / len(data)
            
            if score > best_score:
                best_score = score
                best_masks = (mask_h, mask_t)
                
                if score > 0.95:
                    print(f"  ✨ TROBAT! MaskH=0x{mask_h:X}, MaskT=0x{mask_t:X} -> {score*100:.1f}%")
                    return
                    
    print(f"Millor: MaskH=0x{best_masks[0]:X}, MaskT=0x{best_masks[1]:X} -> {best_score*100:.1f}%")
    
    # Provar funcions més complexes
    print("\nProvant P = f(M, House_Lo, House_Hi, TempDec)...")
    
    # Ex: P = (M + House_Lo + TempDec) & 0xF
    # Ex: P = (M ^ House_Lo ^ House_Hi ^ TempDec) & 0xF
    
    formulas = [
        ("M + H_Lo", lambda d: (d['m'] + (d['house'] & 0xF)) & 0xF),
        ("M + H_Hi", lambda d: (d['m'] + ((d['house'] >> 4) & 0xF)) & 0xF),
        ("M + TDec", lambda d: (d['m'] + d['temp_dec']) & 0xF),
        ("M ^ H_Lo", lambda d: (d['m'] ^ (d['house'] & 0xF)) & 0xF),
        ("M ^ H_Hi", lambda d: (d['m'] ^ ((d['house'] >> 4) & 0xF)) & 0xF),
        ("M ^ TDec", lambda d: (d['m'] ^ d['temp_dec']) & 0xF),
        ("M + H_Lo + TDec", lambda d: (d['m'] + (d['house'] & 0xF) + d['temp_dec']) & 0xF),
        ("M ^ H_Lo ^ TDec", lambda d: (d['m'] ^ (d['house'] & 0xF) ^ d['temp_dec']) & 0xF),
        ("M ^ H_Hi ^ TDec", lambda d: (d['m'] ^ ((d['house'] >> 4) & 0xF) ^ d['temp_dec']) & 0xF),
    ]
    
    for name, func in formulas:
        matches = sum(1 for d in data if func(d) == d['p'])
        score = matches / len(data)
        
        if score > 0.5:
            print(f"  {name}: {score*100:.1f}%")
            if score > 0.95:
                print(f"    ✨ ÈXIT!")
                return

if __name__ == "__main__":
    analyze_p_vs_m()
