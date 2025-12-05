#!/usr/bin/env python3
"""
Analitza House 247: Quan usa cada valor de nibble 7?
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def analyze_house247_nib7():
    data_247 = []
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                if house != 247:
                    continue
                
                temp_c = float(row['temperature_C'])
                channel = int(row['channel'])
                payload_hex = row['payload64_hex']
                
                nibbles = [int(c, 16) for c in payload_hex]
                nib7 = nibbles[7]
                
                data_247.append({
                    'temp': temp_c,
                    'channel': channel,
                    'nib7': nib7,
                    'payload': payload_hex
                })
                
            except (ValueError, KeyError):
                continue
    
    print(f"House 247: {len(data_247)} mostres\n")
    
    # Agrupar per nibble 7
    by_nib7 = {}
    for val in [0x0, 0x1, 0x2, 0x8]:
        by_nib7[val] = [d for d in data_247 if d['nib7'] == val]
    
    print(f"Distribució per Nibble 7:")
    for val in sorted(by_nib7.keys()):
        count = len(by_nib7[val])
        if count > 0:
            temps = [d['temp'] for d in by_nib7[val]]
            t_min = min(temps)
            t_max = max(temps)
            t_avg = sum(temps) / len(temps)
            
            print(f"  Nib7={val:X}: {count:4d} mostres, Temp range: {t_min:5.1f}°C - {t_max:5.1f}°C (avg: {t_avg:5.1f}°C)")
    
    # Mostrar exemples de cada
    print(f"\nExemples:")
    for val in [0x0, 0x1, 0x2, 0x8]:
        if by_nib7[val]:
            example = by_nib7[val][0]
            print(f"  Nib7={val:X}: T={example['temp']:5.1f}°C, Payload={example['payload']}")
    
    # Comprovar si és relacionat amb el decimal de temperatura
    print(f"\nNib7 vs Decimal de temperatura:")
    for val in [0x0, 0x1, 0x2, 0x8]:
        if not by_nib7[val]:
            continue
        
        decimals = [(int(d['temp'] * 10) % 10) for d in by_nib7[val]]
        unique_decimals = sorted(set(decimals))
        
        print(f"  Nib7={val:X}: Decimals={unique_decimals}")

if __name__ == "__main__":
    analyze_house247_nib7()
