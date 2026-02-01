#!/usr/bin/env python3
"""
Analitza què varia entre payloads amb mateix (House, Channel, Temp) però diferent P.
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def analyze_p_variations():
    # Agrupar per (house, channel, temp)
    groups = defaultdict(list)
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                channel = int(row['channel'])
                temp_c = float(row['temperature_C'])
                payload_hex = row['payload64_hex']
                
                temp_rounded = round(temp_c, 1)
                key = (house, channel, temp_rounded)
                
                nibbles = [int(c, 16) for c in payload_hex]
                groups[key].append(nibbles)
                
            except (ValueError, KeyError):
                continue
    
    # Trobar grups amb P diferent
    print("Analitzant grups amb múltiples valors de P:\n")
    
    count = 0
    for key, nibbles_list in groups.items():
        if len(nibbles_list) < 2:
            continue
            
        # Comprovar si P varia
        p_values = [n[14] for n in nibbles_list]
        if len(set(p_values)) <= 1:
            continue
            
        count += 1
        if count > 3:  # Només mostrar primers 3 casos
            continue
            
        house, channel, temp = key
        print(f"House={house}, Channel={channel}, Temp={temp}°C ({len(nibbles_list)} mostres)")
        
        # Comparar nibble a nibble
        for i, nibbles in enumerate(nibbles_list[:3]):  # Primeres 3 mostres
            print(f"  Mostra {i+1}: {[f'{n:X}' for n in nibbles]}")
        
        # Trobar quins nibbles varien
        varying_positions = []
        for pos in range(16):
            values_at_pos = [n[pos] for n in nibbles_list]
            if len(set(values_at_pos)) > 1:
                varying_positions.append(pos)
        
        print(f"  Nibbles que varien: {varying_positions}")
        
        # Mostrar valors als nibbles que varien
        for pos in varying_positions:
            values = [n[pos] for n in nibbles_list]
            print(f"    Pos {pos:2d}: {[f'{v:X}' for v in values[:10]]}")
        
        print()

if __name__ == "__main__":
    analyze_p_variations()
