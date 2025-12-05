#!/usr/bin/env python3
"""
Verifica les transformacions XOR entre diferents nib7 amb TOTES les dades.
"""

import csv
from pathlib import Path
from collections import defaultdict, Counter

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def verify_xor_transformations():
    # Estructura: data[house][nib7][temp_idx] = p
    data = defaultdict(lambda: defaultdict(dict))
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                temp_c = float(row['temperature_C'])
                payload_hex = row['payload64_hex']
                
                nibbles = [int(c, 16) for c in payload_hex]
                nib7 = nibbles[7]
                p = nibbles[14]
                
                temp_idx = int(round((temp_c + 40) * 10))
                
                if temp_idx not in data[house][nib7]:
                    data[house][nib7][temp_idx] = p
                    
            except (ValueError, KeyError):
                continue
    
    print("="*70)
    print("VERIFICACIÓ DE TRANSFORMACIONS XOR")
    print("="*70)
    
    # House 247
    house = 247
    
    # Definir les transformacions esperades
    xor_map = {
        (0, 1): 0xB,
        (0, 2): 0x6,
        (0, 8): None,  # Calcular
        (1, 2): 0xD,
        (1, 8): 0xA,
        (2, 8): 0x7,
    }
    
    print(f"\nHouse {house}:")
    print("-"*70)
    
    for (nib7_a, nib7_b), expected_xor in xor_map.items():
        if nib7_a not in data[house] or nib7_b not in data[house]:
            continue
        
        lut_a = data[house][nib7_a]
        lut_b = data[house][nib7_b]
        
        # Trobar temperatures comunes
        common_temps = set(lut_a.keys()) & set(lut_b.keys())
        
        if len(common_temps) < 5:
            print(f"\nNib7={nib7_a:X} vs Nib7={nib7_b:X}: Poques temperatures en comú ({len(common_temps)})")
            continue
        
        # Calcular XORs
        xors = []
        for temp_idx in common_temps:
            p_a = lut_a[temp_idx]
            p_b = lut_b[temp_idx]
            xor_val = p_a ^ p_b
            xors.append(xor_val)
        
        xor_dist = Counter(xors)
        
        print(f"\nNib7={nib7_a:X} vs Nib7={nib7_b:X} ({len(common_temps)} temps):")
        
        if len(xor_dist) == 1:
            actual_xor = list(xor_dist.keys())[0]
            status = "✅" if expected_xor is None or actual_xor == expected_xor else "⚠️"
            print(f"  {status} XOR constant: 0x{actual_xor:X} (100%)")
            
            if expected_xor and actual_xor != expected_xor:
                print(f"      Esperat: 0x{expected_xor:X}, Real: 0x{actual_xor:X}")
        else:
            most_common_xor, count = xor_dist.most_common(1)[0]
            percentage = count / len(xors) * 100
            
            if percentage > 95:
                print(f"  ⚠️  XOR quasi-constant: 0x{most_common_xor:X} ({percentage:.1f}%)")
            else:
                print(f"  ❌ XOR variable: {len(xor_dist)} valors diferents")
            
            print(f"     Distribució: {dict(xor_dist.most_common(5))}")
    
    # Calcular XOR base per Nib7=0 (si existeix)
    if 0 in data[house]:
        print("\n" + "="*70)
        print("TAULA DE TRANSFORMACIÓ XOR (Base: Nib7=0)")
        print("="*70)
        
        print("\n```python")
        print("NIB7_XOR_TABLE = {")
        
        base_nib7 = 0
        for nib7 in sorted(data[house].keys()):
            if nib7 == base_nib7:
                print(f"    0x{nib7:X}: 0x0,  # Base LUT")
                continue
            
            lut_base = data[house][base_nib7]
            lut_target = data[house][nib7]
            
            common_temps = set(lut_base.keys()) & set(lut_target.keys())
            
            if common_temps:
                xors = [lut_base[t] ^ lut_target[t] for t in common_temps]
                xor_dist = Counter(xors)
                
                if len(xor_dist) == 1:
                    xor_val = list(xor_dist.keys())[0]
                    print(f"    0x{nib7:X}: 0x{xor_val:X},  # P({nib7:X}) = P({base_nib7:X}) XOR 0x{xor_val:X}")
        
        print("}")
        print("```")

if __name__ == "__main__":
    verify_xor_transformations()
