#!/usr/bin/env python3
"""
Proves Avançades: LFSR, Hashes Polinomials, Dependència de R1.
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def lfsr_4bit(seed, taps, iterations):
    """LFSR de 4 bits."""
    state = seed & 0xF
    for _ in range(iterations):
        feedback = 0
        for tap in taps:
            feedback ^= (state >> tap) & 1
        state = ((state << 1) | feedback) & 0xF
    return state

def polynomial_hash(data, poly):
    """Hash polinomial sobre nibbles."""
    h = 0
    for nibble in data:
        h = ((h << 4) ^ nibble) & 0xFF
        # Reduce amb poly
        if h & 0x80:
            h ^= poly
    return h & 0xF

def load_test_data():
    data = []
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                payload_hex = row['payload64_hex']
                r12_val = int(row['R12'], 16)
                
                r1 = (r12_val >> 8) & 0xF
                m = (r12_val >> 4) & 0xF
                p = r12_val & 0xF
                
                nibbles = [int(c, 16) for c in payload_hex]
                
                data.append({
                    'house': house,
                    'nibbles': nibbles,
                    'r1': r1,
                    'm': m,
                    'p': p
                })
            except (ValueError, KeyError):
                continue
    return data

def test_advanced_hypotheses():
    data = load_test_data()
    data_247 = [d for d in data if d['house'] == 247]
    
    print(f"Dataset House 247: {len(data_247)} registres\n")
    
    # 1. LFSR amb seed basat en House
    print("[1] LFSR 4-bit amb seed = House...")
    house_seed = 247 & 0xF  # 0x7
    
    for taps_config in [[0, 1], [1, 2], [2, 3], [0, 3]]:
        # Iterations podria ser TempIdx o M
        matches_temp = 0
        matches_m = 0
        
        for d in data_247:
            temp_iter = sum(d['nibbles']) & 0xFF  # Proxy de temperatura
            m_iter = d['m']
            
            p_pred_temp = lfsr_4bit(house_seed, taps_config, temp_iter)
            p_pred_m = lfsr_4bit(house_seed, taps_config, m_iter)
            
            if p_pred_temp == d['p']: matches_temp += 1
            if p_pred_m == d['p']: matches_m += 1
            
        score_temp = matches_temp / len(data_247)
        score_m = matches_m / len(data_247)
        
        if score_temp > 0.1 or score_m > 0.1:
            print(f"  Taps {taps_config}: TempIter={score_temp*100:.1f}%, MIter={score_m*100:.1f}%")
    
    # 2. Hash Polinomial sobre payload
    print("\n[2] Hash Polinomial sobre nibbles...")
    for poly in [0x07, 0x09, 0x0B, 0x1D, 0x39]:
        matches = 0
        for d in data_247:
            h = polynomial_hash(d['nibbles'], poly)
            if h == d['p']: matches += 1
            
        score = matches / len(data_247)
        if score > 0.1:
            print(f"  Poly 0x{poly:02X}: {score*100:.1f}%")
    
    # 3. P depèn de R1?
    print("\n[3] P = f(R1, M)...")
    
    formulas = [
        ("R1 ^ M", lambda d: d['r1'] ^ d['m']),
        ("R1 + M", lambda d: (d['r1'] + d['m']) & 0xF),
        ("R1 ^ M ^ H_Lo", lambda d: d['r1'] ^ d['m'] ^ (d['house'] & 0xF)),
        ("(R1 << 2) ^ M", lambda d: ((d['r1'] << 2) ^ d['m']) & 0xF),
    ]
    
    for name, func in formulas:
        matches = sum(1 for d in data_247 if func(d) == d['p'])
        score = matches / len(data_247)
        if score > 0.1:
            print(f"  {name}: {score*100:.1f}%")
    
    # 4. P com a checksum de posicions específiques
    print("\n[4] P = Checksum de nibbles específics...")
    
    # Provar diferents combinacions de nibbles
    for mask in [0b111100000000, 0b000011110000, 0b000000001111, 
                 0b101010101010, 0b110011001100]:
        matches = 0
        for d in data_247:
            selected = [d['nibbles'][i] for i in range(12) if (mask >> (11-i)) & 1]
            if selected:
                checksum = sum(selected) & 0xF
                if checksum == d['p']: matches += 1
                
        score = matches / len(data_247)
        if score > 0.1:
            print(f"  Mask {mask:012b}: {score*100:.1f}%")
    
    # 5. P com a rotació de M
    print("\n[5] P = Rotate(M) amb offset...")
    for offset in range(16):
        matches = 0
        for d in data_247:
            # Rotate left
            rotated = ((d['m'] << 1) | (d['m'] >> 3)) & 0xF
            p_pred = (rotated + offset) & 0xF
            if p_pred == d['p']: matches += 1
            
        score = matches / len(data_247)
        if score > 0.1:
            print(f"  Rot(M) + {offset}: {score*100:.1f}%")

if __name__ == "__main__":
    test_advanced_hypotheses()
