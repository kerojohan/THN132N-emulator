#!/usr/bin/env python3
"""
Refinem el Hash Polinomial (49.3%) afegint transformacions.
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def polynomial_hash(data, poly):
    """Hash polinomial sobre nibbles."""
    h = 0
    for nibble in data:
        h = ((h << 4) ^ nibble) & 0xFF
        if h & 0x80:
            h ^= poly
    return h & 0xF

def load_data():
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

def refine_polynomial_hash():
    data = load_data()
    data_247 = [d for d in data if d['house'] == 247]
    
    print(f"Dataset House 247: {len(data_247)} registres\n")
    
    best_poly = 0x07
    
    print(f"Refinant Hash Polinomial (Poly 0x{best_poly:02X})...\n")
    
    # 1. Hash ^ House bits
    for mask in range(16):
        matches = 0
        for d in data_247:
            h = polynomial_hash(d['nibbles'], best_poly)
            p_pred = h ^ ((d['house'] >> mask) & 0xF) if mask < 8 else h ^ (d['house'] & 0xF)
            if p_pred == d['p']: matches += 1
            
        score = matches / len(data_247)
        if score > 0.5:
            print(f"  Hash ^ (House >> {mask if mask < 8 else 0} & 0xF): {score*100:.1f}%")
    
    print()
    
    # 2. Hash ^ M
    matches = sum(1 for d in data_247 if (polynomial_hash(d['nibbles'], best_poly) ^ d['m']) == d['p'])
    print(f"  Hash ^ M: {matches/len(data_247)*100:.1f}%")
    
    # 3. Hash ^ R1
    matches = sum(1 for d in data_247 if (polynomial_hash(d['nibbles'], best_poly) ^ d['r1']) == d['p'])
    print(f"  Hash ^ R1: {matches/len(data_247)*100:.1f}%")
    
    # 4. Hash + offset
    print()
    for offset in range(16):
        matches = sum(1 for d in data_247 if ((polynomial_hash(d['nibbles'], best_poly) + offset) & 0xF) == d['p'])
        score = matches / len(data_247)
        if score > 0.5:
            print(f"  Hash + {offset}: {score*100:.1f}%")
    
    # 5. Hash amb diferents seeds (XOR inicial)
    print("\n  Provant Hash amb seed inicial...")
    test_seeds = [data_247[0]['house'] & 0xF, data_247[0]['m']]
    for seed in test_seeds:
        # Modificar hash per incloure seed
        matches = 0
        for d in data_247:
            h = seed
            for nibble in d['nibbles']:
                h = ((h << 4) ^ nibble) & 0xFF
                if h & 0x80:
                    h ^= best_poly
            h &= 0xF
            if h == d['p']: matches += 1
            
        score = matches / len(data_247)
        if score > 0.5:
            print(f"    Seed {seed}: {score*100:.1f}%")
    
    # 6. Provar tots els polinomis amb XOR M
    print("\n  Provant altres polys amb XOR M...")
    for poly in range(256):
        matches = 0
        for d in data_247:
            h = polynomial_hash(d['nibbles'], poly)
            p_pred = h ^ d['m']
            if p_pred == d['p']: matches += 1
            
        score = matches / len(data_247)
        if score > 0.9:
            print(f"    ✨ TROBAT! Poly 0x{poly:02X}, Hash ^ M: {score*100:.1f}%")
            return

if __name__ == "__main__":
    refine_polynomial_hash()
