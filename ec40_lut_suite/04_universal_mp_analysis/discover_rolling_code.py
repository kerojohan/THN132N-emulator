#!/usr/bin/env python3
"""
Força bruta: Analitza la seqüència temporal EXACTA del nibble 7.
"""

import csv
from pathlib import Path
from datetime import datetime
from collections import Counter

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def discover_rolling_code_pattern():
    # Carregar dades de House 247 amb timestamps
    data_247 = []
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                if house != 247:
                    continue
                
                timestamp_str = row['timestamp']
                payload_hex = row['payload64_hex']
                
                nibbles = [int(c, 16) for c in payload_hex]
                nib7 = nibbles[7]
                
                try:
                    ts = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except:
                    continue
                
                data_247.append({
                    'timestamp': ts,
                    'nib7': nib7,
                    'payload': payload_hex
                })
                
            except (ValueError, KeyError):
                continue
    
    # Ordenar per timestamp
    data_247.sort(key=lambda x: x['timestamp'])
    
    print(f"House 247: {len(data_247)} mostres ordenades temporalment\n")
    
    # Mostrar seqüència temporal
    print("Seqüència temporal del nibble 7:")
    print("Timestamp           | Nib7 | Delta_seg")
    print("--------------------|------|----------")
    
    prev_ts = None
    sequence = []
    
    for i, d in enumerate(data_247[:100]):  # Primeres 100 mostres
        delta_sec = (d['timestamp'] - prev_ts).total_seconds() if prev_ts else 0
        print(f"{d['timestamp']} |  {d['nib7']:X}   | {delta_sec:6.0f}s")
        
        sequence.append(d['nib7'])
        prev_ts = d['timestamp']
    
    # Analitzar transicions
    print(f"\nAnàlisi de transicions:")
    
    transitions = {}
    for i in range(1, len(data_247)):
        prev_nib7 = data_247[i-1]['nib7']
        curr_nib7 = data_247[i]['nib7']
        
        key = f"{prev_nib7:X} -> {curr_nib7:X}"
        transitions[key] = transitions.get(key, 0) + 1
    
    print("\nTransició           | Count")
    print("--------------------|------")
    for trans in sorted(transitions.keys(), key=lambda x: -transitions[x])[:20]:
        print(f"{trans:19s} | {transitions[trans]:5d}")
    
    # Buscar patrons cíclics
    print(f"\nBuscant patrons cíclics...")
    
    # Extreure només la seqüència de nibble 7
    nib7_seq = [d['nib7'] for d in data_247]
    
    # Buscar patró repetit
    for pattern_len in range(2, 20):
        # Comprovar si es repeteix
        is_repeating = True
        for i in range(pattern_len, min(len(nib7_seq), pattern_len * 10)):
            if nib7_seq[i] != nib7_seq[i % pattern_len]:
                is_repeating = False
                break
        
        if is_repeating:
            pattern = nib7_seq[:pattern_len]
            print(f"  ✓ Patró de longitud {pattern_len}: {[f'{n:X}' for n in pattern]}")
    
    # Comprovar si simplement rota entre els valors
    print(f"\nValors únics: {sorted(set(nib7_seq))}")
    print(f"Distribució: {Counter(nib7_seq)}")

if __name__ == "__main__":
    discover_rolling_code_pattern()
