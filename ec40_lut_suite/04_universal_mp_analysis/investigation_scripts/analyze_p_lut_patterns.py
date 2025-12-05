#!/usr/bin/env python3
"""
Analitza la LUT empírica de P per trobar patrons de transformació.
Objectiu: Veure si hi ha regles que permetin generar P de manera més compacta.
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def extract_p_luts_by_nib7():
    """Extreu LUTs de P separades per cada valor de nibble7."""
    
    # Estructura: luts[house][nib7][temp_idx] = p
    luts = defaultdict(lambda: defaultdict(dict))
    
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
                
                # Índex temperatura
                temp_idx = int(round((temp_c + 40) * 10))
                
                # Guardar
                if temp_idx not in luts[house][nib7]:
                    luts[house][nib7][temp_idx] = p
                    
            except (ValueError, KeyError):
                continue
    
    return luts

def analyze_lut_patterns():
    luts = extract_p_luts_by_nib7()
    
    print("="*70)
    print("ANÀLISI DE PATRONS EN LUT EMPÍRICA DE P")
    print("="*70)
    
    # Analitzar House 247 (el més complet)
    house = 247
    
    if house not in luts:
        print(f"House {house} no trobat!")
        return
    
    print(f"\nHouse {house}:")
    print("-"*70)
    
    # Mostrar cobertura per cada nib7
    for nib7 in sorted(luts[house].keys()):
        lut = luts[house][nib7]
        temp_indices = sorted(lut.keys())
        
        if temp_indices:
            temp_min = (min(temp_indices) - 400) / 10
            temp_max = (max(temp_indices) - 400) / 10
            
            print(f"\nNib7={nib7:X}: {len(lut)} punts, rang {temp_min:.1f}°C - {temp_max:.1f}°C")
            
            # Mostrar primers 20 valors
            print(f"  Primers 20 P: {[f'{lut[idx]:X}' for idx in temp_indices[:20]]}")
    
    # Analitzar transformacions entre diferents nib7
    print("\n" + "="*70)
    print("TRANSFORMACIONS ENTRE DIFERENTS NIB7")
    print("="*70)
    
    nib7_values = sorted(luts[house].keys())
    
    if len(nib7_values) < 2:
        print("Necessitem almenys 2 valors de nib7 per analitzar transformacions")
        return
    
    # Comparar nib7 parell a parell
    for i in range(len(nib7_values)):
        for j in range(i+1, len(nib7_values)):
            nib7_a = nib7_values[i]
            nib7_b = nib7_values[j]
            
            lut_a = luts[house][nib7_a]
            lut_b = luts[house][nib7_b]
            
            # Trobar temperatures en comú
            common_temps = set(lut_a.keys()) & set(lut_b.keys())
            
            if len(common_temps) < 10:
                continue
            
            print(f"\nComparant Nib7={nib7_a:X} vs Nib7={nib7_b:X} ({len(common_temps)} temps en comú):")
            
            # Calcular XOR, SUB, ADD
            xors = []
            subs = []
            adds = []
            
            for temp_idx in sorted(common_temps)[:30]:  # Primers 30
                p_a = lut_a[temp_idx]
                p_b = lut_b[temp_idx]
                
                xors.append(p_a ^ p_b)
                subs.append((p_a - p_b) & 0xF)
                adds.append((p_a + p_b) & 0xF)
            
            # Comprovar si són constants
            if len(set(xors)) == 1:
                print(f"  ✅ XOR constant: P({nib7_b:X}) = P({nib7_a:X}) XOR 0x{xors[0]:X}")
            elif len(set(xors)) <= 3:
                from collections import Counter
                xor_dist = Counter(xors)
                print(f"  ⚠️  XOR quasi-constant: {dict(xor_dist)}")
            else:
                print(f"  ❌ XOR no constant (valors únics: {len(set(xors))})")
            
            if len(set(subs)) == 1:
                print(f"  ✅ SUB constant: P({nib7_b:X}) = P({nib7_a:X}) - 0x{subs[0]:X}")
            
            if len(set(adds)) == 1:
                print(f"  ✅ ADD constant: P({nib7_a:X}) + P({nib7_b:X}) = 0x{adds[0]:X}")
    
    # Analitzar patrons interns de cada LUT
    print("\n" + "="*70)
    print("PATRONS INTERNS DE CADA LUT")
    print("="*70)
    
    for nib7 in sorted(luts[house].keys()):
        lut = luts[house][nib7]
        temp_indices = sorted(lut.keys())
        
        if len(temp_indices) < 20:
            continue
        
        print(f"\nNib7={nib7:X}:")
        
        # Calcular diferències consecutives
        diffs = []
        for i in range(1, min(30, len(temp_indices))):
            prev_idx = temp_indices[i-1]
            curr_idx = temp_indices[i]
            
            # Només si són consecutius (diff=1)
            if curr_idx - prev_idx == 1:
                prev_p = lut[prev_idx]
                curr_p = lut[curr_idx]
                diff = (curr_p - prev_p) & 0xF
                diffs.append(diff)
        
        if diffs:
            from collections import Counter
            diff_dist = Counter(diffs)
            print(f"  Diferències consecutives: {dict(diff_dist)}")
            
            if len(set(diffs)) <= 3:
                print(f"  ⚠️  Patró quasi-regular detectat!")

if __name__ == "__main__":
    analyze_lut_patterns()
