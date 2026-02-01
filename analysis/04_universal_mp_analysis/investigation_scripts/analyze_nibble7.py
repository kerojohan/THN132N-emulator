#!/usr/bin/env python3
"""
Investiga el nibble 7 - és un rolling code?
"""

import csv
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def analyze_nibble_7():
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        
        nib7_values = []
        
        for row in reader:
            try:
                payload_hex = row['payload64_hex']
                nibbles = [int(c, 16) for c in payload_hex]
                
                nib7_values.append(nibbles[7])
                
            except (ValueError, KeyError):
                continue
        
        print(f"Distribució del nibble 7 ({len(nib7_values)} mostres):\n")
        
        counter = Counter(nib7_values)
        for value in sorted(counter.keys()):
            count = counter[value]
            pct = count / len(nib7_values) * 100
            print(f"  0x{value:X}: {count:4d} ({pct:5.1f}%)")
        
        print(f"\nConsum únic: {len(counter)} valors diferents")
        
        # Comprovar si és un rolling code (valors consecutius)
        if len(counter) <= 16:
            print("\n  Aquest podria ser un rolling code de 4 bits (0-F)")

if __name__ == "__main__":
    analyze_nibble_7()
