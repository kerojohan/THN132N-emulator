#!/usr/bin/env python3
"""
Verificació del resultat "100%" trobat.
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

def verify_solution():
    data_247 = []
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                if int(row['house']) != 247: continue
                
                payload_hex = row['payload64_hex']
                r12_val = int(row['R12'], 16)
                temp_c = float(row['temperature_C'])
                
                nibbles = [int(c, 16) for c in payload_hex]
                p = r12_val & 0xF
                
                data_247.append({
                    'nibbles': nibbles,
                    'p': p,
                    'temp_c': temp_c,
                    'payload': payload_hex
                })
            except (ValueError, KeyError):
                continue
    
    print(f"Verificant amb {len(data_247)} registres...\n")
    
    # Solució trobada: Poly=0x00, XOR=None, Offset=0
    # P = Hash(nibbles, 0x00) & 0xF
    
    matches = 0
    errors = []
    
    for d in data_247:
        h = polynomial_hash(d['nibbles'], poly=0x00)
        
        if h == d['p']:
            matches += 1
        else:
            if len(errors) < 10:
                errors.append((d['temp_c'], d['payload'], d['p'], h))
    
    print(f"Resultat: {matches}/{len(data_247)} ({matches/len(data_247)*100:.2f}%)")
    
    if errors:
        print(f"\nPrimers {len(errors)} errors:")
        for temp, payload, p_real, p_calc in errors:
            print(f"  T={temp:5.1f}°C, Payload={payload}, P_real={p_real:X}, P_calc={p_calc:X}")
    else:
        print("\n✅ SOLUCIÓ PERFECTA VERIFICADA!")
        print("\nFórmula:")
        print("  P = Hash(payload_nibbles, poly=0x00) & 0xF")
        print("\nOn Hash és:")
        print("  h = 0")
        print("  for nibble in nibbles:")
        print("      h = ((h << 4) ^ nibble) & 0xFF")
        print("  return h & 0xF")

if __name__ == "__main__":
    verify_solution()
