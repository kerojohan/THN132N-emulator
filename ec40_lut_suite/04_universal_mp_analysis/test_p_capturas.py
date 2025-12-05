#!/usr/bin/env python3
"""
Anàlisi Exhaustiva de P amb dades correctes de ec40_capturas_merged.csv.
Prova TOTES les hipòtesis amb el dataset complet.
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def load_full_data():
    data = []
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                temp_c = float(row['temperature_C'])
                payload_hex = row['payload64_hex']
                r12_str = row['R12']
                
                # Extreure M i P del R12
                r12_val = int(r12_str, 16)
                r1 = (r12_val >> 8) & 0xF
                m = (r12_val >> 4) & 0xF
                p = r12_val & 0xF
                
                # Extreure nibbles del payload
                nibbles = [int(c, 16) for c in payload_hex]
                
                # TempIdx i decimal
                t_idx = int(round((temp_c + 40) * 10))
                t_dec = int(round(abs(temp_c) * 10)) % 10
                
                data.append({
                    'house': house,
                    'temp_c': temp_c,
                    'temp_idx': t_idx,
                    'temp_dec': t_dec,
                    'nibbles': nibbles,
                    'r1': r1,
                    'm': m,
                    'p': p
                })
                
            except (ValueError, KeyError):
                continue
                
    return data

def test_all_hypotheses():
    data = load_full_data()
    print(f"Dataset complet: {len(data)} registres")
    
    # Filtrar per House 247 per començar
    data_247 = [d for d in data if d['house'] == 247]
    print(f"House 247: {len(data_247)} registres\n")
    
    # 1. P = f(M, TempDec)
    print("[1] Provant P = M ^ TempDec...")
    matches = sum(1 for d in data_247 if (d['m'] ^ d['temp_dec']) == d['p'])
    print(f"  Score: {matches}/{len(data_247)} ({matches/len(data_247)*100:.1f}%)\n")
    
    # 2. P = f(M, House_Lo)
    print("[2] Provant P = M ^ (House & 0xF)...")
    matches = sum(1 for d in data_247 if (d['m'] ^ (d['house'] & 0xF)) == d['p'])
    print(f"  Score: {matches}/{len(data_247)} ({matches/len(data_247)*100:.1f}%)\n")
    
    # 3. P = f(TempIdx)
    print("[3] Provant P = TempIdx & 0xF...")
    matches = sum(1 for d in data_247 if (d['temp_idx'] & 0xF) == d['p'])
    print(f"  Score: {matches}/{len(data_247)} ({matches/len(data_247)*100:.1f}%)\n")
    
    # 4. P = f(Suma nibbles)
    print("[4] Provant P = Sum(nibbles) & 0xF...")
    for offset in range(16):
        matches = sum(1 for d in data_247 if ((sum(d['nibbles']) + offset) & 0xF) == d['p'])
        if matches / len(data_247) > 0.5:
            print(f"  Offset {offset}: {matches}/{len(data_247)} ({matches/len(data_247)*100:.1f}%)")
    
    # 5. Buscar LUT Base + Offset(House)
    print("\n[5] Analitzant relació entre Houses...")
    
    # Comparar House 247 vs House 3
    data_3 = [d for d in data if d['house'] == 3]
    if data_3:
        print(f"  House 3: {len(data_3)} registres")
        
        # Buscar temps comuns
        p_247 = {d['temp_idx']: d['p'] for d in data_247}
        p_3 = {d['temp_idx']: d['p'] for d in data_3}
        
        common = set(p_247.keys()) & set(p_3.keys())
        print(f"  Temps comuns: {len(common)}")
        
        if common:
            xors = [p_247[t] ^ p_3[t] for t in sorted(common)[:20]]
            print(f"  XORs (primers 20): {xors}")
            unique_xors = set(xors)
            print(f"  XORs únics: {sorted(unique_xors)}")

if __name__ == "__main__":
    test_all_hypotheses()
