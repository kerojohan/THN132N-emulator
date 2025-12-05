#!/usr/bin/env python3
"""
Analitza la relació entre M i la Temperatura per veure si és una funció esglaonada.
També investiga la discrepància en House 95 vs 187.
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent

def load_data():
    CSV_FILES = [
        BASE_DIR / "ec40_live.csv",
        BASE_DIR / "ec40_live_1.csv", 
        BASE_DIR / "ec40_capturas_merged.csv"
    ]
    
    data = []
    for csv_file in CSV_FILES:
        if not csv_file.exists():
            continue
        with open(csv_file, 'r') as f:
            for row in csv.DictReader(f):
                try:
                    data.append(row)
                except:
                    continue
    return data

def extract_m(row):
    checksum_str = row.get('checksum_hex', row.get('R12', ''))
    try:
        r12 = int(checksum_str, 16) if isinstance(checksum_str, str) else int(checksum_str)
        return (r12 >> 4) & 0xF
    except:
        return None

def main():
    print("="*70)
    print("ANÀLISI M vs TEMPERATURA")
    print("="*70)
    
    data = load_data()
    
    # 1. Investigar House 95 vs 187
    print("\n1. Detall House 95 vs 187 (XORs trobats)")
    print("-" * 60)
    
    h95 = defaultdict(list)
    h187 = defaultdict(list)
    
    for row in data:
        try:
            h = int(row['house_code'])
            t = float(row['temp'])
            m = extract_m(row)
            if m is None: continue
            
            if h == 95: h95[t].append(m)
            if h == 187: h187[t].append(m)
        except:
            continue
            
    common_temps = sorted(set(h95.keys()) & set(h187.keys()))
    
    print(f"Temperatures comunes: {len(common_temps)}")
    print("Temp    | M(95)   | M(187)  | XOR")
    print("--------|---------|---------|-----")
    
    xor_counts = defaultdict(int)
    
    for t in common_temps:
        m95_vals = set(h95[t])
        m187_vals = set(h187[t])
        
        # Si hi ha múltiples valors per la mateixa temperatura, això és un problema
        m95_str = ",".join(map(str, m95_vals))
        m187_str = ",".join(map(str, m187_vals))
        
        for m1 in m95_vals:
            for m2 in m187_vals:
                xor = m1 ^ m2
                xor_counts[xor] += 1
                if xor != 0:
                    print(f"{t:6.1f}  | {m95_str:7s} | {m187_str:7s} | 0x{xor:X} <--- DISCREPÀNCIA")
                # else:
                #     print(f"{t:6.1f}  | {m95_str:7s} | {m187_str:7s} | 0x{xor:X}")
    
    print(f"\nResum XORs: {dict(xor_counts)}")
    
    # 2. Veure evolució de M amb la temperatura per House 95
    print("\n2. Evolució M vs Temp (House 95)")
    print("-" * 60)
    
    temps = sorted(h95.keys())
    for t in temps:
        ms = sorted(list(set(h95[t])))
        print(f"{t:5.1f}°C : M={ms}")

if __name__ == "__main__":
    main()
