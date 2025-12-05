#!/usr/bin/env python3
"""
Analitza els nibbles de flags i postamble de les captures reals.
"""

import csv
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def analyze_flags_and_postamble():
    data = []
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                temp_c = float(row['temperature_C'])
                payload_hex = row['payload64_hex']
                
                nibbles = [int(c, 16) for c in payload_hex]
                
                # Posicions:
                # 0-3: ID (EC40)
                # 4: Channel
                # 5-6: House
                # 7: Fixed/Flag?
                # 8-10: Temp
                # 11: Flags/Battery
                # 12-14: Checksum (R1, M, P)
                # 15: Postamble
                
                flag_nibble = nibbles[11]
                postamble = nibbles[15]
                
                data.append({
                    'temp_c': temp_c,
                    'flag': flag_nibble,
                    'postamble': postamble,
                    'payload': payload_hex
                })
                
            except (ValueError, KeyError):
                continue
    
    print(f"Analitzant {len(data)} captures...\n")
    
    # Analitzar flags segons temperatura
    print("NIBBLE DE FLAGS (Posició 11):")
    
    flags_pos = Counter(d['flag'] for d in data)
    print(f"Distribució: {dict(flags_pos)}")
    
    # Separar per temperatura positiva/negativa
    flags_pos_temp = Counter(d['flag'] for d in data if d['temp_c'] >= 0)
    flags_neg_temp = Counter(d['flag'] for d in data if d['temp_c'] < 0)
    
    print(f"\nTemperatures positives (>= 0°C): {dict(flags_pos_temp)}")
    print(f"Temperatures negatives (< 0°C): {dict(flags_neg_temp)}")
    
    # Analitzar postamble
    print("\n" + "="*50)
    print("\nNIBBLE POSTAMBLE (Posició 15):")
    
    postamble_dist = Counter(d['postamble'] for d in data)
    print(f"Distribució: {dict(postamble_dist)}")
    
    # Exemples
    print("\nExemples:")
    for d in data[:10]:
        print(f"  T={d['temp_c']:5.1f}°C, Flag=0x{d['flag']:X}, Post=0x{d['postamble']:X}, Payload={d['payload']}")

if __name__ == "__main__":
    analyze_flags_and_postamble()
