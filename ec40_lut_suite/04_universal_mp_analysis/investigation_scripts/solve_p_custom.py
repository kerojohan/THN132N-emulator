#!/usr/bin/env python3
"""
Solver P: Hipòtesis Aritmètiques i Lògiques Personalitzades.
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CSV_FILE = BASE_DIR / "ec40_live.csv"

def get_nibbles(hex_str):
    return [int(c, 16) for c in hex_str]

def load_data():
    data = []
    with open(CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = row['raw64']
            checksum_hex = row['checksum_hex']
            if not raw or not checksum_hex: continue
            try:
                payload_str = raw[:12]
                nibbles = get_nibbles(payload_str)
                target_p = int(checksum_hex[-1], 16)
                
                # També necessitem M (penúltim nibble)
                m = int(checksum_hex[-2], 16)
                
                data.append({
                    'nibbles': nibbles,
                    'm': m,
                    'target': target_p
                })
            except:
                continue
    return data

def solve_custom(data):
    print(f"Provant hipòtesis personalitzades amb {len(data)} mostres...")
    
    # 1. P depèn de M?
    # P = M ^ K
    # P = (M + K) & 0xF
    # P = Rotate(M) ^ K
    
    print("\n[1] P vs M...")
    for k in range(16):
        diffs_xor = set()
        diffs_add = set()
        
        for d in data:
            diffs_xor.add(d['target'] ^ d['m'])
            diffs_add.add((d['target'] - d['m']) & 0xF)
            
        if len(diffs_xor) == 1:
            print(f"  ✨ P = M ^ 0x{list(diffs_xor)[0]:X}")
            return
        if len(diffs_add) == 1:
            print(f"  ✨ P = (M + {list(diffs_add)[0]}) & 0xF")
            return

    # 2. P depèn de la suma de nibbles (però diferent de M)
    # M = Sum & 0xF
    # P = (Sum >> 4) & 0xF ? (No, això seria R1)
    # P = (Sum ^ (Sum >> 4)) & 0xF ?
    
    print("\n[2] P vs Suma de Nibbles...")
    for d in data:
        s = sum(d['nibbles'])
        d['sum'] = s
        
    # Test: P = f(Sum)
    # P = (Sum >> K) & 0xF
    # P = Sum ^ K
    
    for k in range(16):
        diffs = set()
        for d in data:
            val = (d['sum'] ^ k) & 0xF
            if val == d['target']: matches = True
            else: matches = False
            # Això no és correcte, busquem patró global
            
    # Busquem relació directa Sum -> P
    sum_to_p = {}
    consistent = True
    for d in data:
        s = d['sum']
        p = d['target']
        if s in sum_to_p and sum_to_p[s] != p:
            consistent = False
            # print(f"  Inconsistent: Sum {s} -> P {sum_to_p[s]} vs {p}")
            break
        sum_to_p[s] = p
        
    if consistent:
        print("  ✨ P està determinat únicament per la Suma Total!")
        print("  Mapeig Sum -> P:")
        for s in sorted(sum_to_p.keys()):
            print(f"    Sum 0x{s:X} -> P 0x{sum_to_p[s]:X}")
    else:
        print("  ❌ P no depèn només de la Suma (mateixa suma dóna diferents P).")

    # 3. P depèn de Suma Parells/Senars
    print("\n[3] P vs Suma Parells/Senars...")
    odd_even_consistent = True
    map_oe = {}
    
    for d in data:
        s_even = sum(d['nibbles'][0::2])
        s_odd = sum(d['nibbles'][1::2])
        key = (s_even & 0xF, s_odd & 0xF)
        
        p = d['target']
        if key in map_oe and map_oe[key] != p:
            odd_even_consistent = False
            break
        map_oe[key] = p
        
    if odd_even_consistent:
        print("  ✨ P depèn de (SumEven & 0xF, SumOdd & 0xF)!")
    else:
        print("  ❌ P no depèn només de SumEven/SumOdd.")

if __name__ == "__main__":
    data = load_data()
    solve_custom(data)
