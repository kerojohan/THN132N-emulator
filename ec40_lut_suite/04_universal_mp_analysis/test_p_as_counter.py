#!/usr/bin/env python3
"""
ÚLTIMA HIPÒTESI: P és un contador/rolling code independent que
cicla a través de tots els valors 0-F.
"""

import csv
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent  
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def analyze_p_as_counter():
    # Carregar dades de House 247 amb timestamp
    data_247 = []
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                if house != 247:
                    continue
                
                timestamp_str = row['timestamp']
                temp_c = float(row['temperature_C'])
                payload_hex = row['payload64_hex']
                
                nibbles = [int(c, 16) for c in payload_hex]
                nib7 = nibbles[7]
                p = nibbles[14]
                
                try:
                    ts = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except:
                    continue
                
                data_247.append({
                    'timestamp': ts,
                    'temp': temp_c,
                    'nib7': nib7,
                    'p': p
                })                
            except (ValueError, KeyError):
                continue
    
    # Ordenar per timestamp
    data_247.sort(key=lambda x: x['timestamp'])
    
    print(f"House 247: {len(data_247)} mostres temporals\n")
    
    # Mostrar seqüència de P
    print("Seqüència temporal de P:")
    print("Timestamp           | Nib7 | P  | DeltaP")
    print("--------------------|------|----|---------")
    
    prev_p = None
    p_sequence = []
    
    for i, d in enumerate(data_247[:50]):
        delta_p = (d['p'] - prev_p) & 0xF if prev_p is not None else 0
        print(f"{d['timestamp']} |  {d['nib7']:X}   | {d['p']:2X} |   {delta_p:+2d}")
        
        p_sequence.append(d['p'])
        prev_p = d['p']
    
    # Comprovar si P incrementa
    print(f"\nPrimers 50 valors de P: {[f'{p:X}' for p in p_sequence[:50]]}")
    
    # Comprovar si està relacionat amb índex temporal
    print(f"\nProvant si P = f(timestamp_mod_16)...")
    
    # Usar el primer timestamp com a referència
    t0 = data_247[0]['timestamp']
    
    matches = 0
    for d in data_247:
        seconds_since_start = (d['timestamp'] - t0).total_seconds()
        
        # Provar diferents mòduls
        for mod in [16, 32, 64, 128, 256]:
            idx = int(seconds_since_start) % mod
            if (idx & 0xF) == d['p']:
                matches += 1
                break
    
    print(f"  Matches amb timestamp mod: {matches}/{len(data_247)} ({matches/len(data_247)*100:.1f}%)")

if __name__ == "__main__":
    analyze_p_as_counter()
