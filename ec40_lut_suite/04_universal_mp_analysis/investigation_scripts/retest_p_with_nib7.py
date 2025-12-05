#!/usr/bin/env python3
"""
RE-TEST de P incloent el nibble 7 variable en el càlcul.
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def test_p_with_all_nibbles():
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        
        algorithms = {
            'XOR_shift [0:15] (AMB nib7)': lambda n: xor_shift(n[:15]),
            'XOR_shift [0:14]': lambda n: xor_shift(n[:14]),
            'XOR_shift [0:13]': lambda n: xor_shift(n[:13]),
            'XOR_shift [0:12]': lambda n: xor_shift(n[:12]),
        }
        
        results = {name: 0 for name in algorithms}
        total = 0
        
        for row in reader:
            try:
                payload_hex = row['payload64_hex']
                nibbles = [int(c, 16) for c in payload_hex]
                
                p_real = nibbles[14]
                
                for name, func in algorithms.items():
                    if func(nibbles) == p_real:
                        results[name] += 1
                        
                total += 1
                
            except (ValueError, KeyError):
                continue
        
        print(f"Resultats INCLOENT nibble 7 variable ({total} mostres):\n")
        
        for name, matches in sorted(results.items(), key=lambda x: -x[1]):
            pct = matches / total * 100
            status = "✅" if pct > 99 else "⚠️" if pct > 90 else "❌"
            print(f"{status} {name:35s}: {matches:4d}/{total} ({pct:5.1f}%)")

def xor_shift(nibbles):
    h = 0
    for nib in nibbles:
        h = ((h << 4) ^ nib) & 0xFF
    return h & 0xF

if __name__ == "__main__":
    test_p_with_all_nibbles()
