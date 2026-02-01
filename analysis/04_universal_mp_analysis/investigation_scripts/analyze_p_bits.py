#!/usr/bin/env python3
"""
Analitza si els bits de P depenen de bits específics del House Code.
Intenta trobar correlacions bit a bit.
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "04_universal_mp_analysis" / "golden_master.csv"

def analyze_bit_dependencies():
    # Carregar dades: (House, Temp) -> P
    data_points = []
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            h = int(row['house'])
            t = int(row['temp_idx'])
            p = int(row['p'])
            data_points.append((h, t, p))
            
    print(f"Analitzant {len(data_points)} punts de dades...")
    
    # Per cada bit de P (0..3), busquem quins bits de House (0..7) hi influeixen.
    # Per fer-ho, busquem parells de punts amb MATEIXA Temperatura però DIFERENT House.
    # Si P canvia, ha de ser per culpa del House.
    
    # Agrupar per Temp
    by_temp = defaultdict(list)
    for h, t, p in data_points:
        by_temp[t].append((h, p))
        
    # Matriu de correlació: [P_bit][H_bit] -> Score
    # Score: Quants cops canvia P_bit quan canvia H_bit (mantenint la resta igual? difícil)
    
    # Mètode alternatiu: Força bruta de funcions booleanes simples
    # P_bit[i] = XOR(subset of House bits) ^ XOR(subset of Temp bits)?
    # Però Temp és complex.
    
    # Simplificació:
    # P[i] = Base_P[i](Temp) ^ Mask[i](House)
    # On Mask[i](House) és una funció XOR de bits del House.
    
    # Pas 1: Determinar "Base P" (per una House referència, ex 95)
    # Pas 2: Calcular "Diff P" per altres houses.
    # Pas 3: Veure si Diff P depèn linealment dels bits del House.
    
    ref_h = 95
    ref_lut = {}
    for h, t, p in data_points:
        if h == ref_h:
            ref_lut[t] = p
            
    print(f"House Referència {ref_h}: {len(ref_lut)} punts.")
    
    # Recollir (House, P_Diff) per punts on tenim ref_lut[t]
    samples = [] # (House, P_Diff)
    
    for h, t, p in data_points:
        if h == ref_h: continue
        if t in ref_lut:
            p_ref = ref_lut[t]
            p_diff = p ^ p_ref
            samples.append((h, p_diff))
            
    print(f"Mostres comparatives: {len(samples)}")
    
    # Ara busquem: P_Diff_bit[b] = XOR(subset of House bits)
    # House bits: 0..7
    
    for bit_p in range(4): # 0..3
        print(f"\nAnalitzant Bit {bit_p} de P_Diff...")
        
        # Provem totes les màscares de House (2^8 = 256)
        # Hipòtesi: P_Diff_bit = Parity(House & Mask)
        
        best_mask = -1
        best_score = -1
        
        for mask in range(256):
            matches = 0
            total = 0
            
            for h, diff in samples:
                # Target bit
                target = (diff >> bit_p) & 1
                
                # Predict bit: Parity of (h & mask)
                # Count bits set in (h & mask)
                val = h & mask
                parity = bin(val).count('1') % 2
                
                if parity == target:
                    matches += 1
                total += 1
            
            if total == 0: continue
            score = matches / total
            
            if score > best_score:
                best_score = score
                best_mask = mask
                
            if score == 1.0:
                print(f"  ✨ TROBAT! P_Diff[{bit_p}] = Parity(House & 0x{mask:X})")
                # No fem break, volem veure si n'hi ha més (redundants)
                
        print(f"  Millor Mask: 0x{best_mask:X} (Score: {best_score*100:.1f}%)")

if __name__ == "__main__":
    analyze_bit_dependencies()
