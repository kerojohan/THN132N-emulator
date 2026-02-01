#!/usr/bin/env python3
"""
Analitza els 8 grups de House Code (Key = House & 0x0B)
i intenta ajustar una funció lineal per trams del tipus:
M = ((T + Offset) >> Shift) & 0xF
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "04_universal_mp_analysis" / "golden_master.csv"

def load_data_by_group():
    groups = defaultdict(list)
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            h = int(row['house'])
            t = int(row['temp_idx'])
            m = int(row['m'])
            
            key = h & 0x0B
            groups[key].append((t, m))
    return groups

def fit_function(points):
    """
    Intenta trobar Offset i Shift que maximitzin els encerts per:
    M = ((T + Offset) >> Shift) & 0xF
    """
    best_score = -1
    best_params = None
    
    total_points = len(points)
    if total_points == 0:
        return None
        
    # Espai de cerca
    # Shift: normalment 4, 5, 6 per índexs de 0-255
    # Offset: pot ser qualsevol valor
    
    for shift in range(3, 8):
        for offset in range(-300, 300):
            matches = 0
            for t, m in points:
                pred = ((t + offset) >> shift) & 0xF
                if pred == m:
                    matches += 1
            
            if matches > best_score:
                best_score = matches
                best_params = (shift, offset)
                
                if matches == total_points: # Perfecte
                    return (shift, offset, 1.0)
                    
    return (best_params[0], best_params[1], best_score / total_points)

def main():
    print("="*70)
    print("AJUST DE FUNCIÓ M = ((T + Offset) >> Shift)")
    print("="*70)
    
    groups = load_data_by_group()
    
    results = []
    
    for key in sorted(groups.keys()):
        points = groups[key]
        print(f"\nGRUP 0x{key:X} ({len(points)} punts):")
        
        # Filtrar conflictes (mateix T, diferent M)
        # Ens quedem amb el més freqüent per T
        t_map = defaultdict(list)
        for t, m in points:
            t_map[t].append(m)
            
        clean_points = []
        for t, ms in t_map.items():
            # Moda
            most_common = max(set(ms), key=ms.count)
            clean_points.append((t, most_common))
            
        shift, offset, score = fit_function(clean_points)
        
        print(f"  Millor ajust: Shift={shift}, Offset={offset}")
        print(f"  Precisió: {score*100:.1f}%")
        
        results.append((key, shift, offset, score))
        
        # Mostrar alguns exemples
        print("  Exemples (T -> M_real vs M_pred):")
        for i, (t, m) in enumerate(clean_points[:5]):
            pred = ((t + offset) >> shift) & 0xF
            print(f"    T={t:3d} -> {m} vs {pred} {'✅' if m==pred else '❌'}")

    print("\n" + "="*70)
    print("RESUM PARÀMETRES")
    print("="*70)
    print("Key | Shift | Offset | Score")
    print("----|-------|--------|-------")
    for key, s, o, sc in results:
        print(f"0x{key:X} | {s:5d} | {o:6d} | {sc*100:.1f}%")

if __name__ == "__main__":
    main()
