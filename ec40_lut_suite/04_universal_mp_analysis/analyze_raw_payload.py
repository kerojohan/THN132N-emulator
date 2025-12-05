#!/usr/bin/env python3
"""
Analitza la relació entre raw168 i payload64 per entendre el postamble.
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def analyze_raw_vs_payload():
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        
        print("Comparant RAW168 vs PAYLOAD64:\n")
        
        for i, row in enumerate(reader):
            if i >= 5: break
            
            raw168 = row['raw168_hex']
            payload64 = row['payload64_hex']
            
            print(f"Mostra {i+1}:")
            print(f"  RAW168:    {raw168}")
            print(f"  PAYLOAD64: {payload64}")
            print(f"  Longitud RAW: {len(raw168)} chars, PAYLOAD: {len(payload64)} chars")
            
            # El payload hauria de ser 16 nibbles (64 bits)
            if len(payload64) == 16:
                print(f"  ✓ Payload té 16 nibbles (correcte)")
            else:
                print(f"  ✗ Payload té {len(payload64)} nibbles (esperat 16)")
            
            print()

if __name__ == "__main__":
    analyze_raw_vs_payload()
