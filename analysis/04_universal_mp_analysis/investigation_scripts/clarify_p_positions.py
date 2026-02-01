#!/usr/bin/env python3
"""
Clarificació de posicions: [0:15] són 15 nibbles (posicions 0-14), NO 16!
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def calc_p_xor(nibbles):
    h = 0
    for nib in nibbles:
        h = ((h << 4) ^ nib) & 0xFF
    return h & 0xF

# Agafar primer exemple
with open(DATA_FILE, 'r') as f:
    reader = csv.DictReader(f)
    row = next(reader)
    
    payload = row['payload64_hex']
    nibbles = [int(c, 16) for c in payload]
    
    print(f"Payload: {payload}")
    print(f"Nibbles: {[f'{n:X}' for n in nibbles]}")
    print(f"Índexs:  {list(range(len(nibbles)))}\n")
    
    print("Identificant cada nibble:")
    print(f"  [0-3]:   ID = {payload[0:4]} (EC40)")
    print(f"  [4]:     Channel = {nibbles[4]:X}")
    print(f"  [5-6]:   House = {nibbles[5]:X}{nibbles[6]:X}")
    print(f"  [7]:     Fixed = {nibbles[7]:X}")
    print(f"  [8-10]:  Temp = {nibbles[8]:X}{nibbles[9]:X}{nibbles[10]:X}")
    print(f"  [11]:    Flags = {nibbles[11]:X}")
    print(f"  [12]:    R1 = {nibbles[12]:X}")
    print(f"  [13]:    M = {nibbles[13]:X}")
    print(f"  [14]:    P = {nibbles[14]:X}")
    print(f"  [15]:    Postamble = {nibbles[15]:X}\n")
    
    print("Provant diferents rangs per P:")
    
    # [0:12] = posicions 0-11 (12 nibbles, sense checksum)
    p_calc = calc_p_xor(nibbles[0:12])
    print(f"  P sobre [0:12] (12 nibbles, sense checksum): {p_calc:X}")
    
    # [0:13] = posicions 0-12 (13 nibbles, inclou R1)
    p_calc = calc_p_xor(nibbles[0:13])
    print(f"  P sobre [0:13] (13 nibbles, amb R1):         {p_calc:X}")
    
    # [0:14] = posicions 0-13 (14 nibbles, inclou R1, M)
    p_calc = calc_p_xor(nibbles[0:14])
    print(f"  P sobre [0:14] (14 nibbles, amb R1, M):      {p_calc:X}")
    
    # [0:15] = posicions 0-14 (15 nibbles, inclou R1, M, P)!!!
    p_calc = calc_p_xor(nibbles[0:15])
    print(f"  P sobre [0:15] (15 nibbles, amb R1, M, P):   {p_calc:X} ← ERA AIXÒ!")
    
    print(f"\n  P real (posició 14): {nibbles[14]:X}")
    
    print("\n⚠️  ATENCIÓ: nibbles[0:15] són les posicions 0-14 (15 elements)")
    print("     Això INCLOU el mateix P a la posició 14!")
    print("     Així que SÍ que és auto-referencial.")
    
    print("\nPer tant, el problema és que l'algorisme XOR té una propietat:")
    print("  Per QUALSEVOL nibble afegit al final, el resultat és igual a aquest nibble.")
    print("  Això passa quan el XOR acumulat dels 14 primers nibbles és 0.")
    
    # Verificar
    xor_14 = calc_p_xor(nibbles[0:14])
    print(f"\n  XOR acumulat de [0:14]: {xor_14:X}")
    
    if xor_14 == 0:
        print("  ✓ Efectivament és 0, per això qualsevol P és auto-consistent!")
    else:
        print(f"  ✗ No és 0, hauria de ser {xor_14:X}")
        
    # Provar la fórmula correcta
    print("\n🔍 Si XOR[0:14]=0, aleshores P = (XOR[0:14] + P) & 0xF = (0 + P) & 0xF = P")
    print("   Això explica per què tots els valors són auto-consistents!")

if __name__ == "__main__":
    pass
