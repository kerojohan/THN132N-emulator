#!/usr/bin/env python3
"""
Investiga exactament sobre quins nibbles es calcula P.
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def calculate_p_variant(nibbles, range_spec):
    """Calcula P sobre un rang específic de nibbles."""
    h = 0
    for nibble in range_spec:
        h = ((h << 4) ^ nibble) & 0xFF
    return h & 0xF

def test_p_ranges():
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        
        # Acumular resultats per cada variant
        variants = {
            'P sobre [0:12]': 0,  # Primers 12 (sense checksum)
            'P sobre [0:13]': 0,  # Fins R1 (inclòs)
            'P sobre [0:14]': 0,  # Fins M (inclòs)
            'P sobre [0:15]': 0,  # Fins P exclòs
            'P sobre [0:16]': 0,  # Tot el payload
        }
        
        total = 0
        
        for row in reader:
            try:
                payload_hex = row['payload64_hex']
                nibbles = [int(c, 16) for c in payload_hex]
                
                p_real = nibbles[14]  # Posició 14 és P
                
                # Provar cada variant
                if calculate_p_variant(nibbles, nibbles[0:12]) == p_real:
                    variants['P sobre [0:12]'] += 1
                    
                if calculate_p_variant(nibbles, nibbles[0:13]) == p_real:
                    variants['P sobre [0:13]'] += 1
                    
                if calculate_p_variant(nibbles, nibbles[0:14]) == p_real:
                    variants['P sobre [0:14]'] += 1
                    
                if calculate_p_variant(nibbles, nibbles[0:15]) == p_real:
                    variants['P sobre [0:15]'] += 1
                    
                if calculate_p_variant(nibbles, nibbles[0:16]) == p_real:
                    variants['P sobre [0:16]'] += 1
                    
                total += 1
                
            except (ValueError, KeyError):
                continue
        
        print(f"Resultats (total: {total} mostres):\n")
        
        for variant, matches in variants.items():
            pct = matches / total * 100
            status = "✅" if matches == total else "❌"
            print(f"{status} {variant}: {matches}/{total} ({pct:.1f}%)")
        
        # Provar exemples individuals
        print("\n" + "="*50)
        print("\nExemple detallat (primera mostra):")
        
        with open(DATA_FILE, 'r') as f2:
            reader2 = csv.DictReader(f2)
            row = next(reader2)
            
            payload_hex = row['payload64_hex']
            nibbles = [int(c, 16) for c in payload_hex]
            
            print(f"  Payload: {payload_hex}")
            print(f"  Nibbles: {[f'{n:X}' for n in nibbles]}")
            print(f"  P real (pos 14): {nibbles[14]:X}")
            
            for i in range(12, 17):
                if i <= len(nibbles):
                    p_calc = calculate_p_variant(nibbles, nibbles[0:i])
                    match = "✓" if p_calc == nibbles[14] else "✗"
                    print(f"  {match} P sobre [0:{i}]: {p_calc:X}")

if __name__ == "__main__":
    test_p_ranges()
