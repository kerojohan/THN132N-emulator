#!/usr/bin/env python3
"""
REVISIÓ COMPLETA: Quin és REALMENT l'algoritme de P?
Tornem a provar TOTS els algoritmes sobre [0:15].
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def test_all_p_algorithms():
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        
        algorithms = {
            'XOR_shift [0:15]': lambda nib15: xor_shift(nib15),
            'XOR_shift [0:14]': lambda nib15: xor_shift(nib15[:14]),
            'Simple_XOR [0:15]': lambda nib15: simple_xor(nib15),
            'Simple_XOR [0:14]': lambda nib15: simple_xor(nib15[:14]),
            'Sum [0:14]': lambda nib15: sum(nib15[:14]) & 0xF,
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
        
        print(f"Resultats (total: {total} mostres):\n")
        
        for name, matches in sorted(results.items(), key=lambda x: -x[1]):
            pct = matches / total * 100
            status = "✅" if matches == total else "❌"
            print(f"{status} {name:25s}: {matches:4d}/{total} ({pct:5.1f}%)")

def xor_shift(nibbles):
    h = 0
    for nib in nibbles:
        h = ((h << 4) ^ nib) & 0xFF
    return h & 0xF

def simple_xor(nibbles):
    x = 0
    for nib in nibbles:
        x ^= nib
    return x & 0xF

if __name__ == "__main__":
    test_all_p_algorithms()
