#!/usr/bin/env python3
"""
Investiga el patró XOR [6, 11, 13] entre House 3 i 247.
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def investigate_xor_pattern():
    # Carregar dades
    data_by_house = {}
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                temp_c = float(row['temperature_C'])
                r12_val = int(row['R12'], 16)
                p = r12_val & 0xF
                
                t_idx = int(round((temp_c + 40) * 10))
                t_dec = int(round(abs(temp_c) * 10)) % 10
                
                if house not in data_by_house:
                    data_by_house[house] = {}
                    
                data_by_house[house][t_idx] = {'p': p, 'temp_dec': t_dec, 'temp_c': temp_c}
                
            except (ValueError, KeyError):
                continue
                
    # Comparar House 3 vs 247
    h3 = data_by_house.get(3, {})
    h247 = data_by_house.get(247, {})
    
    common_temps = sorted(set(h3.keys()) & set(h247.keys()))
    
    print(f"Temps comuns: {len(common_temps)}")
    print("\nTempC  | TDec | P(3) | P(247) | XOR | XOR_bin")
    print("-------|------|------|--------|-----|--------")
    
    # Agrupar per XOR
    by_xor = {}
    by_tdec = {}
    
    for t in common_temps:
        p3 = h3[t]['p']
        p247 = h247[t]['p']
        tdec = h3[t]['temp_dec']
        temp_c = h3[t]['temp_c']
        
        xor_val = p3 ^ p247
        
        if xor_val not in by_xor:
            by_xor[xor_val] = []
        by_xor[xor_val].append((temp_c, tdec))
        
        if tdec not in by_tdec:
            by_tdec[tdec] = []
        by_tdec[tdec].append(xor_val)
        
        if len(by_xor) <= 20: # Mostrar primers casos
            print(f"{temp_c:6.1f} | {tdec:4d} | {p3:4X} | {p247:6X} | {xor_val:3X} | {xor_val:04b}")
            
    print(f"\nDistribució per XOR:")
    for xor_val in sorted(by_xor.keys()):
        print(f"  XOR {xor_val} (0x{xor_val:X}, {xor_val:04b}): {len(by_xor[xor_val])} casos")
        
    print(f"\nDistribució per TempDec:")
    for tdec in sorted(by_tdec.keys()):
        xors_this_dec = by_tdec[tdec]
        unique_xors = sorted(set(xors_this_dec))
        print(f"  TDec={tdec}: XORs={unique_xors} ({len(xors_this_dec)} mostr es)")
        
    # Hipòtesi: XOR depèn del bit de TempDec?
    # 6 = 0110, 11 = 1011, 13 = 1101
    # Diferències: bit 0, 2, 3?
    
    print("\nAnàlisi de bits:")
    print("XOR  6 = 0110")
    print("XOR 11 = 1011")
    print("XOR 13 = 1101")
    
    # Provem: XOR[bit] vs TempDec[bit]
    print("\nCorrelació XOR vs TempDec:")
    
    for bit in range(4):
        # Comptar coincidències
        match = 0
        total = 0
        
        for t in common_temps:
            tdec = h3[t]['temp_dec']
            xor_val = h3[t]['p'] ^ h247[t]['p']
            
            xor_bit = (xor_val >> bit) & 1
            tdec_bit = (tdec >> bit) & 1
            
            if xor_bit == tdec_bit:
                match += 1
            total += 1
            
        print(f"  Bit {bit}: {match}/{total} ({match/total*100:.1f}%)")

if __name__ == "__main__":
    investigate_xor_pattern()
