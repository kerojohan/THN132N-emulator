#!/usr/bin/env python3
"""
Prova de força bruta: Amb nibble 7 conegut, qualsevol P funciona?
O només un valor específic?
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def xor_shift(nibbles):
    h = 0
    for nib in nibbles:
        h = ((h << 4) ^ nib) & 0xFF
    return h & 0xF

# Agafar primer exemple
with open(DATA_FILE, 'r') as f:
    reader = csv.DictReader(f)
    row = next(reader)
    
    payload_hex = row['payload64_hex']
    nibbles = [int(c, 16) for c in payload_hex]
    
    print(f"Payload: {payload_hex}")
    print(f"Nibbles: {[f'{n:X}' for n in nibbles]}\n")
    
    # Nibbles [0-13]: ID, Channel, House, Nib7, Temp, Flags, R1, M
    nibbles_14 = nibbles[:14]
    p_real = nibbles[14]
    
    print(f"Nibbles fins M (0-13): {[f'{n:X}' for n in nibbles_14]}")
    print(f"P real: {p_real:X}\n")
    
    print("Provant tots els valors de P (0-F):")
    for p_test in range(16):
        nibbles_15_test = nibbles_14 + [p_test]
        p_calc = xor_shift(nibbles_15_test)
        
        match = "✓" if p_calc == p_real else "✗"
        self_consistent = "SELF!" if p_calc == p_test else ""
        
        print(f"  {match} P={p_test:X}: XOR_shift([...14..., {p_test:X}]) = {p_calc:X} {self_consistent}")
    
    print(f"\nConclusions:")
    print(f"  - Si només hi ha UN valor que funciona: Podem trobar P per força bruta!")
    print(f"  - Si TOTS els valors són auto-consistents: Tenim un problema circular.")
