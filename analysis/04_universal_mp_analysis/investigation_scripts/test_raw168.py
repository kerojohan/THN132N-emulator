#!/usr/bin/env python3
"""
Última hipòtesi: P es genera del RAW168 (Manchester) no del payload decodat.
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def test_raw168_hypothesis():
    data = []
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                raw168 = row['raw168_hex']
                payload64 = row['payload64_hex']
                r12_val = int(row['R12'], 16)
                
                p = r12_val & 0xF
                m = (r12_val >> 4) & 0xF
                
                data.append({
                    'house': house,
                    'raw168': raw168,
                    'payload': payload64,
                    'm': m,
                    'p': p
                })
            except (ValueError, KeyError):
                continue
                
    data_247 = [d for d in data if d['house'] == 247]
    
    print(f"Dataset House 247: {len(data_247)} registres\n")
    
    # 1. Checksum sobre raw168
    print("[1] Checksum sobre RAW168 complet...")
    
    for d in data_247[:5]:
        raw_bytes = bytes.fromhex(d['raw168'])
        
        # Simple sum
        s = sum(raw_bytes) & 0xF
        
        # XOR acumulat
        x = 0
        for b in raw_bytes:
            x ^= b
        x &= 0xF
        
        print(f"  Payload: {d['payload']}")
        print(f"  P real: {d['p']}")
        print(f"  Sum(raw168) & 0xF: {s}")
        print(f"  XOR(raw168) & 0xF: {x}")
        print()
    
    # 2. Provar sistemàticament
    print("[2] Proves sistemàtiques sobre RAW168...")
    
    # Sum
    matches = 0
    for d in data_247:
        raw_bytes = bytes.fromhex(d['raw168'])
        s = sum(raw_bytes) & 0xF
        if s == d['p']: matches += 1
    print(f"  Sum(raw168) & 0xF: {matches}/{len(data_247)} ({matches/len(data_247)*100:.1f}%)")
    
    # XOR
    matches = 0
    for d in data_247:
        raw_bytes = bytes.fromhex(d['raw168'])
        x = 0
        for b in raw_bytes:
            x ^= b
        x &= 0xF
        if x == d['p']: matches += 1
    print(f"  XOR(raw168) & 0xF: {matches}/{len(data_247)} ({matches/len(data_247)*100:.1f}%)")
    
    # Últims N bytes
    for n in [1, 2, 3, 4, 5]:
        matches = 0
        for d in data_247:
            raw_bytes = bytes.fromhex(d['raw168'])
            last_bytes = raw_bytes[-n:]
            s = sum(last_bytes) & 0xF
            if s == d['p']: matches += 1
               
        score = matches / len(data_247)
        if score > 0.1:
            print(f"  Sum(last {n} bytes) & 0xF: {score*100:.1f}%")
    
    print("\n[3] Conclusió...")
    print("  Si cap d'aquests dona >90%, P NO es genera del raw168.")

if __name__ == "__main__":
    test_raw168_hypothesis()
