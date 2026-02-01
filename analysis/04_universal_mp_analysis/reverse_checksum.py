#!/usr/bin/env python3
"""
Intenta fer enginyeria inversa del checksum (3 nibbles) a partir de les dades raw.
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CSV_FILE = BASE_DIR / "ec40_live.csv"

def get_nibbles(hex_str):
    return [int(c, 16) for c in hex_str]

def solve_checksum():
    data = []
    with open(CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = row['raw64']
            checksum_hex = row['checksum_hex']
            
            # Raw inclou el checksum al final?
            # raw: ec401da21810243a
            # checksum: 0x243
            # Sembla que raw conté tot.
            # Payload (sense checksum) seria els primers caràcters.
            # Checksum són els caràcters 12, 13, 14? (0-indexed)
            # e c 4 0 1 d a 2 1 8 1 0 [2 4 3] a
            # 0 1 2 3 4 5 6 7 8 9 0 1  2 3 4  5
            
            # Payload nibbles: 0-11
            # Checksum nibbles: 12-14
            
            if not raw or not checksum_hex: continue
            
            try:
                target = int(checksum_hex, 16)
                payload_str = raw[:12]
                payload_nibbles = get_nibbles(payload_str)
                
                data.append((payload_nibbles, target))
            except:
                continue
                
    print(f"Carregats {len(data)} registres per anàlisi.")
    
    # Provar algoritmes
    # 1. Suma de nibbles
    print("\nProvant Suma de Nibbles...")
    matches = 0
    for nibbles, target in data:
        s = sum(nibbles)
        if s == target: matches += 1
        
    print(f"  Direct Sum: {matches}/{len(data)}")
    
    # 2. Suma de bytes
    print("\nProvant Suma de Bytes...")
    matches = 0
    offset_matches = {}
    
    for nibbles, target in data:
        # Bytes: (0,1), (2,3), ...
        bytes_val = []
        for i in range(0, len(nibbles), 2):
            b = (nibbles[i] << 4) | nibbles[i+1]
            bytes_val.append(b)
            
        s = sum(bytes_val)
        if s == target: matches += 1
        
        diff = target - s
        offset_matches[diff] = offset_matches.get(diff, 0) + 1
        
    print(f"  Byte Sum: {matches}/{len(data)}")
    print(f"  Offsets comuns: {sorted(offset_matches.items(), key=lambda x: x[1], reverse=True)[:5]}")
    
    # 3. Suma de bytes amb nibbles invertits (LSN first)
    print("\nProvant Suma de Bytes (Nibbles Invertits)...")
    matches = 0
    offset_matches = {}
    
    for nibbles, target in data:
        bytes_val = []
        for i in range(0, len(nibbles), 2):
            b = (nibbles[i+1] << 4) | nibbles[i] # Invertit
            bytes_val.append(b)
            
        s = sum(bytes_val)
        if s == target: matches += 1
        
        diff = target - s
        offset_matches[diff] = offset_matches.get(diff, 0) + 1
        
    print(f"  Byte Sum (Inv): {matches}/{len(data)}")
    print(f"  Offsets comuns: {sorted(offset_matches.items(), key=lambda x: x[1], reverse=True)[:5]}")

    # 4. Oregon Scientific v2.1 specific (sum nibbles, but specific logic)
    # Sovint: Sum - 0xA
    
    # 5. Provar de deduir la constant
    # Si Byte Sum dóna un offset constant, ja ho tenim.
    
if __name__ == "__main__":
    solve_checksum()
