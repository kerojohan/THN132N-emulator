#!/usr/bin/env python3
"""
Analitza el comportament de P en funció de la Temperatura.
Comprova si P actua com a bits de menor pes (fine grain).
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "04_universal_mp_analysis" / "golden_master.csv"

def analyze_p():
    # Carregar dades només per House 95 (té moltes dades i bon rang)
    # També podem mirar House 121
    target_houses = [95, 121, 18]
    
    data = defaultdict(list)
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            h = int(row['house'])
            if h in target_houses:
                t = int(row['temp_idx'])
                p = int(row['p'])
                m = int(row['m'])
                data[h].append((t, m, p))
                
    print("="*70)
    print("ANÀLISI DE P vs TEMPERATURA")
    print("="*70)
    
    for h in target_houses:
        points = sorted(data[h])
        if not points: continue
        
        print(f"\nHouse {h} (0x{h:X}):")
        print("TempIdx | Temp(C) | M | P | (M<<4)|P | P (diff)")
        print("--------|---------|---|---|----------|---------")
        
        prev_p = None
        for i, (t, m, p) in enumerate(points):
            # Mostrem només un subconjunt per no saturar
            if i % 5 != 0 and i != 0 and i != len(points)-1:
                continue
                
            temp_c = (t / 10.0) - 40.0
            combined = (m << 4) | p
            
            p_diff = ""
            if prev_p is not None:
                diff = (p - prev_p) & 0xF
                p_diff = f"{diff:+d}"
            
            print(f"{t:7d} | {temp_c:7.1f} | {m} | {p:2d}| {combined:8d} | {p_diff}")
            prev_p = p

if __name__ == "__main__":
    analyze_p()
