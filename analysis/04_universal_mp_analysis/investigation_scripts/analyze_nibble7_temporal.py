#!/usr/bin/env python3
"""
Analitza el nibble 7 en seqüència temporal per veure si és un rolling code.
"""

import csv
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def analyze_nibble7_temporal():
    # Carregar dades amb timestamp
    data = []
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                timestamp_str = row['timestamp']
                house = int(row['house'])
                channel = int(row['channel'])
                temp_c = float(row['temperature_C'])
                payload_hex = row['payload64_hex']
                
                nibbles = [int(c, 16) for c in payload_hex]
                nib7 = nibbles[7]
                
                # Parse timestamp
                try:
                    ts = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except:
                    continue
                
                data.append({
                    'timestamp': ts,
                    'house': house,
                    'channel': channel,
                    'temp': temp_c,
                    'nib7': nib7,
                    'payload': payload_hex
                })
                
            except (ValueError, KeyError):
                continue
    
    # Ordenar per timestamp
    data.sort(key=lambda x: x['timestamp'])
    
    print(f"Analitzant seqüència temporal del nibble 7 ({len(data)} mostres)\n")
    
    # Agrupar per House
    from collections import defaultdict
    by_house = defaultdict(list)
    
    for d in data:
        by_house[d['house']].append(d)
    
    # Analitzar cada house
    for house in sorted(by_house.keys())[:3]:  # Primers 3 houses
        house_data = by_house[house]
        
        print(f"House {house} (0x{house:X}): {len(house_data)} mostres")
        
        # Mostrar seqüència de nibble 7
        nib7_sequence = [d['nib7'] for d in house_data[:20]]
        print(f"  Seqüència nibble 7 (primeres 20): {[f'{n:X}' for n in nib7_sequence]}")
        
        # Comprovar si incrementa
        increments = []
        for i in range(1, min(20, len(house_data))):
            prev_nib7 = house_data[i-1]['nib7']
            curr_nib7 = house_data[i]['nib7']
            diff = (curr_nib7 - prev_nib7) & 0xF
            increments.append(diff)
        
        print(f"  Increments: {[f'{d:X}' for d in increments]}")
        
        # Comprovar si hi ha patró
        unique_increments = set(increments)
        if len(unique_increments) == 1:
            print(f"  ✓ Increment constant: {list(unique_increments)[0]}")
        elif len(unique_increments) <= 3:
            print(f"  ⚠️  Increments semi-regulars: {sorted(unique_increments)}")
        else:
            print(f"  ✗ Increments caòtics: {len(unique_increments)} valors diferents")
        
        # Comprovar correlació amb temperatura
        temps = [d['temp'] for d in house_data[:20]]
        print(f"  Temperatures: {[f'{t:.1f}' for t in temps[:10]]}...")
        
        print()

if __name__ == "__main__":
    analyze_nibble7_temporal()
