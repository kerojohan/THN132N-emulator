#!/usr/bin/env python3
"""
Neteja el dataset: Una sola mostra per (House, Channel, Temp).
Després re-testa tots els algoritmes de P.
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def clean_and_test():
    # Carregar i deduplicar
    unique_samples = {}  # (house, channel, temp_rounded) -> nibbles
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                channel = int(row['channel'])
                temp_c = float(row['temperature_C'])
                payload_hex = row['payload64_hex']
                
                # Arrodonir temperatura a 0.1°C per agrupar
                temp_rounded = round(temp_c, 1)
                
                key = (house, channel, temp_rounded)
                nibbles = [int(c, 16) for c in payload_hex]
                
                # Si ja existeix, comprovar que P sigui el mateix
                if key in unique_samples:
                    if unique_samples[key][14] != nibbles[14]:
                        print(f"⚠️  CONFLICTE: H={house}, Ch={channel}, T={temp_rounded}°C")
                        print(f"    P1={unique_samples[key][14]:X}, P2={nibbles[14]:X}")
                else:
                    unique_samples[key] = nibbles
                    
            except (ValueError, KeyError):
                continue
    
    print(f"Dataset original: {len(list(csv.DictReader(open(DATA_FILE))))} files")
    print(f"Dataset net: {len(unique_samples)} mostres úniques\n")
    
    # Ara re-testejar algoritmes
    algorithms = {
        'XOR_shift [0:12]': lambda nib: xor_shift(nib[:12]),
        'XOR_shift [0:13]': lambda nib: xor_shift(nib[:13]),
        'XOR_shift [0:14]': lambda nib: xor_shift(nib[:14]),
        'Simple_XOR [0:12]': lambda nib: simple_xor(nib[:12]),
        'Simple_XOR [0:13]': lambda nib: simple_xor(nib[:13]),
        'Simple_XOR [0:14]': lambda nib: simple_xor(nib[:14]),
        'Sum [0:12]': lambda nib: sum(nib[:12]) & 0xF,
        'Sum [0:13]': lambda nib: sum(nib[:13]) & 0xF,
        'Sum [0:14]': lambda nib: sum(nib[:14]) & 0xF,
    }
    
    results = {name: 0 for name in algorithms}
    total = len(unique_samples)
    
    for nibbles in unique_samples.values():
        p_real = nibbles[14]
        
        for name, func in algorithms.items():
            if func(nibbles) == p_real:
                results[name] += 1
    
    print(f"Resultats amb dataset net ({total} mostres):\n")
    
    for name, matches in sorted(results.items(), key=lambda x: -x[1]):
        pct = matches / total * 100
        status = "✅" if pct > 90 else "⚠️" if pct > 50 else "❌"
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
    clean_and_test()
