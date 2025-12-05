#!/usr/bin/env python3
"""
Analitza si P(House) = P(Ref) + Offset(House).
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "04_universal_mp_analysis" / "golden_master.csv"

def analyze_offsets():
    data_points = []
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            h = int(row['house'])
            t = int(row['temp_idx'])
            p = int(row['p'])
            data_points.append((h, t, p))
            
    ref_h = 95
    ref_lut = {}
    for h, t, p in data_points:
        if h == ref_h:
            ref_lut[t] = p
            
    print(f"Ref House {ref_h}: {len(ref_lut)} punts.")
    
    # Per cada House, calculem la diferència mitjana amb Ref
    house_diffs = defaultdict(list)
    
    for h, t, p in data_points:
        if h == ref_h: continue
        if t in ref_lut:
            p_ref = ref_lut[t]
            diff = (p - p_ref) & 0xF
            house_diffs[h].append(diff)
            
    print("\nResultats Offset (ADD):")
    for h, diffs in sorted(house_diffs.items()):
        # Check consistency
        unique_diffs = sorted(set(diffs))
        most_common = max(set(diffs), key=diffs.count)
        count = diffs.count(most_common)
        percent = count / len(diffs) * 100
        
        print(f"  House {h} (0x{h:X}): {len(diffs)} pts. Unique={unique_diffs}. Mode={most_common} ({percent:.1f}%)")
        
        if len(unique_diffs) == 1:
            print(f"    ✨ OFFSET CONSTANT: {unique_diffs[0]}")

if __name__ == "__main__":
    analyze_offsets()
