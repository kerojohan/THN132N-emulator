#!/usr/bin/env python3
"""
Analitza el patró XOR de P entre TOTES les parelles de Houses.
Objectiu: Trobar si el patró temperature-dependent es repeteix.
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def load_p_tables():
    """Carrega taules P per cada house."""
    houses = defaultdict(dict)
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                temp_c = float(row['temperature_C'])
                r12_val = int(row['R12'], 16)
                p = r12_val & 0xF
                
                t_idx = int(round((temp_c + 40) * 10))
                houses[house][t_idx] = {'p': p, 'temp_c': temp_c}
                
            except (ValueError, KeyError):
                continue
                
    return houses

def analyze_all_pairs():
    houses = load_p_tables()
    
    # Filtrar houses amb prou dades (>50 punts)
    valid_houses = {h: data for h, data in houses.items() if len(data) > 50}
    house_ids = sorted(valid_houses.keys())
    
    print(f"Houses vàlides: {house_ids}")
    print(f"  (amb >50 punts de dades)\n")
    
    # Analitzar totes les parelles
    results = []
    
    for i, h1 in enumerate(house_ids):
        for h2 in house_ids[i+1:]:
            # Trobar temps comuns
            common_temps = sorted(set(valid_houses[h1].keys()) & set(valid_houses[h2].keys()))
            
            if len(common_temps) < 20:
                continue
                
            # Calcular XORs
            xors_by_temp = []
            for t in common_temps:
                p1 = valid_houses[h1][t]['p']
                p2 = valid_houses[h2][t]['p']
                temp_c = valid_houses[h1][t]['temp_c']
                xor_val = p1 ^ p2
                xors_by_temp.append((temp_c, xor_val))
                
            # Estadístiques
            unique_xors = sorted(set([x for _, x in xors_by_temp]))
            
            # Dividir per rangs de temperatura
            low_temp_xors = [x for t, x in xors_by_temp if t < 18]
            mid_temp_xors = [x for t, x in xors_by_temp if 18 <= t < 24]
            high_temp_xors = [x for t, x in xors_by_temp if t >= 24]
            
            results.append({
                'h1': h1,
                'h2': h2,
                'common': len(common_temps),
                'unique_xors': unique_xors,
                'low_xors': sorted(set(low_temp_xors)) if low_temp_xors else [],
                'mid_xors': sorted(set(mid_temp_xors)) if mid_temp_xors else [],
                'high_xors': sorted(set(high_temp_xors)) if high_temp_xors else [],
            })
            
    # Mostrar resultats
    print("Parelles amb XOR quasi-constant o temperatura-dependent:\n")
    
    for r in results:
        if len(r['unique_xors']) <= 5:  # Màx 5 XORs diferents
            print(f"House {r['h1']} vs {r['h2']} ({r['common']} punts comuns):")
            print(f"  XORs únics: {r['unique_xors']}")
            print(f"  Low temp (<18°C):  {r['low_xors']}")
            print(f"  Mid temp (18-24°C): {r['mid_xors']}")
            print(f"  High temp (>24°C):  {r['high_xors']}")
            
            # Check patró similar a 3 vs 247
            if 0 in r['high_xors'] or len(r['high_xors']) == 1:
                print(f"  ✨ PATRÓ SIMILAR! (XOR convergeix a {r['high_xors']})")
            print()

if __name__ == "__main__":
    analyze_all_pairs()
