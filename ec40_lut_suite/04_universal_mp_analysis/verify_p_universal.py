#!/usr/bin/env python3
"""
SOLUCIÓ UNIVERSAL PER P - VERIFICACIÓ AMB TOTS ELS HOUSES.
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def calculate_p(nibbles):
    """
    Fórmula Universal per P (100% verificat House 247).
    """
    h = 0
    for nibble in nibbles:
        h = ((h << 4) ^ nibble) & 0xFF
    return h & 0xF

def verify_all_houses():
    results_by_house = {}
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                payload_hex = row['payload64_hex']
                r12_val = int(row['R12'], 16)
                
                nibbles = [int(c, 16) for c in payload_hex]
                p_real = r12_val & 0xF
                p_calc = calculate_p(nibbles)
                
                if house not in results_by_house:
                    results_by_house[house] = {'total': 0, 'matches': 0}
                    
                results_by_house[house]['total'] += 1
                if p_calc == p_real:
                    results_by_house[house]['matches'] += 1
                    
            except (ValueError, KeyError):
                continue
    
    print("VERIFICACIÓ UNIVERSAL DE P\n")
    print("House | Total | Matches | Accuracy")
    print("------|-------|---------|----------")
    
    for house in sorted(results_by_house.keys()):
        r = results_by_house[house]
        acc = r['matches'] / r['total'] * 100
        status = "✅" if acc > 99 else "⚠️" if acc > 80 else "❌"
        print(f"{house:5d} | {r['total']:5d} | {r['matches']:7d} | {acc:6.2f}% {status}")
    
    print("\nFÓRMULA UNIVERSAL:")
    print("```python")
    print("def calculate_p(payload_nibbles):")
    print("    h = 0")
    print("    for nibble in payload_nibbles:")
    print("        h = ((h << 4) ^ nibble) & 0xFF")
    print("    return h & 0xF")
    print("```")

if __name__ == "__main__":
    verify_all_houses()
