#!/usr/bin/env python3
"""
Crea una Taula P Base i regles de transformació XOR per cada House.
Hipòtesi: P(House) = P_Base(Temp) ^ XOR_Transform(House, Temp)
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def load_complete_data():
    """Carrega totes les dades amb payload complet."""
    data = []
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                temp_c = float(row['temperature_C'])
                payload_hex = row['payload64_hex']
                r12_val = int(row['R12'], 16)
                
                r1 = (r12_val >> 8) & 0xF
                m = (r12_val >> 4) & 0xF
                p = r12_val & 0xF
                
                nibbles = [int(c, 16) for c in payload_hex]
                t_idx = int(round((temp_c + 40) * 10))
                
                data.append({
                    'house': house,
                    'temp_c': temp_c,
                    'temp_idx': t_idx,
                    'nibbles': nibbles,
                    'r1': r1,
                    'm': m,
                    'p': p
                })
                
            except (ValueError, KeyError):
                continue
                
    return data

def find_p_base_and_transform():
    data = load_complete_data()
    
    # Utilitzem House 3 com a "base" (té moltes dades)
    base_house = 3
    data_base = [d for d in data if d['house'] == base_house]
    
    # Crear P_Base
    p_base = {}
    for d in data_base:
        t = d['temp_idx']
        if t not in p_base:
            p_base[t] = d['p']
            
    print(f"P_Base (House {base_house}): {len(p_base)} punts")
    
    # Per cada altre house, calcular XOR necessari
    houses = sorted(set(d['house'] for d in data))
    
    for h in houses:
        if h == base_house:
            continue
            
        data_h = [d for d in data if d['house'] == h]
        
        # Calcular XOR Transform
        xor_transforms = {}
        for d in data_h:
            t = d['temp_idx']
            if t in p_base:
                xor_needed = d['p'] ^ p_base[t]
                temp_c = d['temp_c']
                
                if temp_c not in xor_transforms:
                    xor_transforms[temp_c] = []
                xor_transforms[temp_c].append(xor_needed)
                
        if not xor_transforms:
            continue
            
        # Analitzar consistència
        consistent_temps = []
        for temp_c, xors in xor_transforms.items():
            if len(set(xors)) == 1:  # Tots els XORs iguals per aquesta temp
                consistent_temps.append((temp_c, xors[0]))
                
        if len(consistent_temps) > 10:
            print(f"\nHouse {h} (0x{h:X}):")
            print(f"  Temps consistents: {len(consistent_temps)}/{len(xor_transforms)}")
            
            # Mostrar patró
            sorted_temps = sorted(consistent_temps)
            
            # Agrupar per XOR
            by_xor = defaultdict(list)
            for temp_c, xor_val in sorted_temps:
                by_xor[xor_val].append(temp_c)
                
            print(f"  Patró XOR:")
            for xor_val in sorted(by_xor.keys()):
                temps = by_xor[xor_val]
                t_min = min(temps)
                t_max = max(temps)
                print(f"    XOR {xor_val:2d} (0x{xor_val:X}): {t_min:5.1f}°C - {t_max:5.1f}°C ({len(temps)} punts)")
                
            # Intentar trobar regla
            # Si XOR depèn del rang de temperatura...
            print(f"  Regla hipotètica:")
            for xor_val in sorted(by_xor.keys()):
                temps = by_xor[xor_val]
                t_ranges = []
                
                # Buscar rangs continus
                temps_sorted = sorted(temps)
                if temps_sorted:
                    start = temps_sorted[0]
                    end = temps_sorted[0]
                    
                    for t in temps_sorted[1:]:
                        if abs(t - end) < 2.0:  # Contigu (marge 2°C)
                            end = t
                        else:
                            t_ranges.append((start, end))
                            start = t
                            end = t
                    t_ranges.append((start, end))
                    
                if len(t_ranges) <= 3:
                    for r_start, r_end in t_ranges:
                        print(f"    if {r_start:.1f} <= T <= {r_end:.1f}: P = P_Base ^ 0x{xor_val:X}")

if __name__ == "__main__":
    find_p_base_and_transform()
