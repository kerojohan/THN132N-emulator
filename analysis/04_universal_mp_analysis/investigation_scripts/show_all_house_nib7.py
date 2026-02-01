#!/usr/bin/env python3
"""
Mostra TOTS els House -> Nib7 mappings.
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def show_all_mappings():
    house_nib7_map = defaultdict(set)
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                payload_hex = row['payload64_hex']
                
                nibbles = [int(c, 16) for c in payload_hex]
                nib7 = nibbles[7]
                
                house_nib7_map[house].add(nib7)
                
            except (ValueError, KeyError):
                continue
    
    print(f"House | Nib7 | House_Lo | House_Hi | Suma | XOR | Paritat")
    print(f"------|------|----------|----------|------|-----|--------")
    
    for house in sorted(house_nib7_map.keys()):
        nib7_values = sorted(house_nib7_map[house])
        
        if len(nib7_values) == 1:
            nib7 = nib7_values[0]
            house_lo = house & 0xF
            house_hi = (house >> 4) & 0xF
            suma = (house_lo + house_hi) & 0xF
            xor = house_lo ^ house_hi
            paritat = bin(house).count('1') % 2
            
            print(f"{house:5d} |  {nib7:X}   |    {house_lo:X}     |    {house_hi:X}     |  {suma:X}   |  {xor:X}  |   {paritat}")
        else:
            print(f"{house:5d} | VARIA: {[f'{n:X}' for n in nib7_values]}")

if __name__ == "__main__":
    show_all_mappings()
