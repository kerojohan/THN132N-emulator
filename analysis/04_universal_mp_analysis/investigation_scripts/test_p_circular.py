#!/usr/bin/env python3
"""
Investiga el càlcul circular de P: P forma part del seu propi càlcul?
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def calculate_p_with_placeholder(nibbles_14, p_placeholder):
    """Calcula P incloent un placeholder per P mateix."""
    nibbles_15 = nibbles_14 + [p_placeholder]
    h = 0
    for nibble in nibbles_15:
        h = ((h << 4) ^ nibble) & 0xFF
    return h & 0xF

# Provar si podem trobar P iterativament
with open(DATA_FILE, 'r') as f:
    reader = csv.DictReader(f)
    
    print("Provant càlcul iteratiu de P:\n")
    
    for i, row in enumerate(reader):
        if i >= 5: break
        
        payload_hex = row['payload64_hex']
        nibbles = [int(c, 16) for c in payload_hex]
        
        p_real = nibbles[14]
        nibbles_14 = nibbles[:14]  # Primers 14 (sense P)
        
        print(f"Mostra {i+1}: {payload_hex}")
        print(f"  P real: {p_real:X}")
        
        # Provar tots els valors possibles de P (0-F)
        for p_test in range(16):
            p_calc = calculate_p_with_placeholder(nibbles_14, p_test)
            if p_calc == p_real:
                if p_test == p_real:
                    print(f"  ✓ Solució: P={p_test:X} (auto-consistent)")
                else:
                    print(f"  ? P placeholder={p_test:X} -> calc={p_calc:X}")
        
        # Algorisme iteratiu: començar amb P=0 i iterar
        p_iter = 0
        for iteration in range(10):
            p_new = calculate_p_with_placeholder(nibbles_14, p_iter)
            if p_new == p_iter:
                status = "✓" if p_new == p_real else "✗"
                print(f"  {status} Iteració {iteration}: P estable a {p_new:X}")
                break
            p_iter = p_new
        
        print()

if __name__ == "__main__":
    pass
