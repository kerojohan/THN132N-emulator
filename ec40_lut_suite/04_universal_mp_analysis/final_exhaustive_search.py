#!/usr/bin/env python3
"""
Recerca FINAL: Brute force complet de (Poly, XOR_Param, Offset).
Buscar la millor combinació possible.
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def polynomial_hash(data, poly, init=0):
    h = init
    for nibble in data:
        h = ((h << 4) ^ nibble) & 0xFF
        if h & 0x80:
            h ^= poly
    return h & 0xF

def load_data_247():
    data = []
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                if int(row['house']) != 247: continue
                
                payload_hex = row['payload64_hex']
                r12_val = int(row['R12'], 16)
                
                nibbles = [int(c, 16) for c in payload_hex]
                r1 = (r12_val >> 8) & 0xF
                m = (r12_val >> 4) & 0xF
                p = r12_val & 0xF
                
                data.append({
                    'nibbles': nibbles,
                    'r1': r1,
                    'm': m,
                    'p': p
                })
            except (ValueError, KeyError):
                continue
    return data

def final_exhaustive_search():
    data = load_data_247()
    print(f"Dataset: {len(data)} registres\n")
    
    best_score = 0
    best_params = None
    
    print("Iniciant recerca exhaustiva...")
    print("Espai: 256 polys x 16 XOR_params x 16 offsets = 65,536 combinacions\n")
    
    # Optimització: Precalcular hashes per cada poly
    hash_cache = {}
    for poly in range(256):
        if poly % 64 == 0:
            print(f"Progress: Poly {poly}/256...")
        
        hashes = [polynomial_hash(d['nibbles'], poly) for d in data]
        hash_cache[poly] = hashes
    
    print("\nBuscant millor combinació...")
    
    # Provar combinacions
    for poly in range(256):
        hashes = hash_cache[poly]
        
        # XOR amb diferents params
        for xor_source in range(5):  # 0=None, 1=M, 2=R1, 3=House(0xF7&0xF), 4=House>>4
            for offset in range(16):
                matches = 0
                
                for i, d in enumerate(data):
                    h = hashes[i]
                    
                    # Apply XOR
                    if xor_source == 1:
                        h ^= d['m']
                    elif xor_source == 2:
                        h ^= d['r1']
                    elif xor_source == 3:
                        h ^= 0x7  # House 247 & 0xF
                    elif xor_source == 4:
                        h ^= 0xF  # House 247 >> 4
                    
                    # Apply offset
                    h = (h + offset) & 0xF
                    
                    if h == d['p']:
                        matches += 1
                
                score = matches / len(data)
                
                if score > best_score:
                    best_score = score
                    best_params = (poly, xor_source, offset)
                    
                    if score > 0.9:
                        xor_names = ['None', 'M', 'R1', 'House_Lo', 'House_Hi']
                        print(f"\n✨ POSSIBLE SOLUCIÓ!")
                        print(f"  Poly: 0x{poly:02X}")
                        print(f"  XOR: {xor_names[xor_source]}")
                        print(f"  Offset: {offset}")
                        print(f"  Score: {score*100:.2f}%")
                        return
    
    # Mostrar millor resultat
    xor_names = ['None', 'M', 'R1', 'House_Lo', 'House_Hi']
    poly, xor_src, offset = best_params
    
    print(f"\n Millor resultat trobat:")
    print(f"  Poly: 0x{poly:02X}")
    print(f"  XOR: {xor_names[xor_src]}")
    print(f"  Offset: {offset}")
    print(f"  Score: {best_score*100:.2f}%")
    print(f"\n  P = (Hash(nibbles, 0x{poly:02X}) ^ {xor_names[xor_src]} + {offset}) & 0xF")

if __name__ == "__main__":
    final_exhaustive_search()
