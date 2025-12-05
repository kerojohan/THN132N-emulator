#!/usr/bin/env python3
"""
Analitza les taules P de TOTS els House IDs disponibles.
Objectiu: Trobar una relació universal (ex: XOR constant) entre taules.
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "04_universal_mp_analysis" / "golden_master.csv"

def load_p_luts():
    # House -> {TempIdx -> P}
    luts = defaultdict(dict)
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            h = int(row['house'])
            t = int(row['temp_idx'])
            p = int(row['p'])
            
            # Guardem el valor (assumim consistència o agafem l'últim)
            luts[h][t] = p
            
    # Filtrar houses amb poques dades
    valid_luts = {}
    for h, lut in luts.items():
        if len(lut) > 20: # Mínim 20 punts per comparar
            valid_luts[h] = lut
            
    return valid_luts

def analyze_relationships(luts):
    houses = sorted(luts.keys())
    print(f"Analitzant {len(houses)} House IDs: {[hex(h) for h in houses]}")
    
    # Agafem House 95 (0x5F) com a referència (té moltes dades)
    ref_h = 95
    if ref_h not in luts:
        ref_h = houses[0]
        
    print(f"\nComparant amb Referència House {ref_h} (0x{ref_h:X})...")
    
    results = []
    
    for h in houses:
        if h == ref_h: continue
        
        # Comparar P[h] vs P[ref] per temperatures comunes
        common_temps = sorted(set(luts[h].keys()) & set(luts[ref_h].keys()))
        
        if not common_temps:
            print(f"  House {h}: 0 punts comuns.")
            continue
            
        xors = []
        diffs = []
        
        for t in common_temps:
            p_h = luts[h][t]
            p_ref = luts[ref_h][t]
            
            xors.append(p_h ^ p_ref)
            diffs.append((p_h - p_ref) & 0xF)
            
        # Analitzar consistència
        unique_xors = sorted(set(xors))
        unique_diffs = sorted(set(diffs))
        
        match_type = "❌ Caòtic"
        val = ""
        
        if len(unique_xors) == 1:
            match_type = "✅ XOR CONSTANT"
            val = f"0x{unique_xors[0]:X}"
            results.append({'h': h, 'type': 'XOR', 'val': unique_xors[0]})
        elif len(unique_diffs) == 1:
            match_type = "✅ DIFF CONSTANT"
            val = f"{unique_diffs[0]}"
            results.append({'h': h, 'type': 'ADD', 'val': unique_diffs[0]})
        elif len(unique_xors) <= 2:
             match_type = f"⚠️ XOR Quasi-Constant ({unique_xors})"
        
        print(f"  House {h} (0x{h:X}): {len(common_temps)} pts. {match_type} {val}")

    # Si trobem patrons XOR, intentem deduir la regla del XOR
    xor_results = [r for r in results if r['type'] == 'XOR']
    if xor_results:
        print("\nAnalitzant patró dels XORs...")
        print(f"  Ref House: 0x{ref_h:X}")
        for r in xor_results:
            h = r['h']
            xor_val = r['val']
            
            # Hipòtesi: XOR_Val = f(House, RefHouse)
            # Ex: XOR_Val = (House ^ RefHouse) & Mask?
            
            h_xor = h ^ ref_h
            print(f"  House 0x{h:X} -> P_XOR 0x{xor_val:X}. (House^Ref = 0x{h_xor:X})")
            
            # Check nibbles
            # Si P_XOR == (House^Ref) & 0xF -> Depèn del nibble baix
            # Si P_XOR == ((House^Ref) >> 4) & 0xF -> Depèn del nibble alt
            
            if xor_val == (h_xor & 0xF):
                print("    -> Coincideix amb (H ^ Ref) & 0xF (Nibble Baix)")
            if xor_val == ((h_xor >> 4) & 0xF):
                print("    -> Coincideix amb ((H ^ Ref) >> 4) & 0xF (Nibble Alt)")

if __name__ == "__main__":
    luts = load_p_luts()
    analyze_relationships(luts)
