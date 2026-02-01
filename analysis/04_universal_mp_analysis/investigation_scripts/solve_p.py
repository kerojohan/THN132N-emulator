#!/usr/bin/env python3
"""
Solver de Força Bruta especialitzat per P.
"""

import csv
import time
from pathlib import Path
from collections import namedtuple

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "04_universal_mp_analysis" / "golden_master.csv"

Record = namedtuple('Record', ['h', 't', 'm', 'p'])

def load_data():
    data = []
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(Record(
                h=int(row['house']),
                t=int(row['temp_idx']),
                m=int(row['m']),
                p=int(row['p'])
            ))
    return data

def solve_p(data):
    print(f"Buscant P amb {len(data)} registres...")
    
    best_score = -1
    
    # Hipòtesis
    # P = (T + Offset) & 0xF  (Simple counter)
    # P = ((T + Offset) >> Shift) & 0xF
    # P = (T ^ Mask) & 0xF
    # P = LUT[T % 16] ^ H
    
    # 1. Check Linear: P = (T + Offset) & 0xF
    print("Provant P = (T + Offset) & 0xF ...")
    for offset in range(256):
        matches = 0
        for r in data:
            if ((r.t + offset) & 0xF) == r.p:
                matches += 1
        score = matches / len(data)
        if score > best_score:
            best_score = score
            print(f"  Millor: {score*100:.1f}% -> (T + {offset}) & 0xF")

    # 2. Check XOR: P = (T ^ Mask) & 0xF
    print("Provant P = (T ^ Mask) & 0xF ...")
    for mask in range(256):
        matches = 0
        for r in data:
            if ((r.t ^ mask) & 0xF) == r.p:
                matches += 1
        score = matches / len(data)
        if score > best_score:
            best_score = score
            print(f"  Millor: {score*100:.1f}% -> (T ^ {mask}) & 0xF")
            
    # 3. Check with House: P = ((T + Offset) ^ House) & 0xF
    print("Provant P = ((T + Offset) ^ House) & 0xF ...")
    for offset in range(256):
        matches = 0
        for r in data:
            if (((r.t + offset) ^ r.h) & 0xF) == r.p:
                matches += 1
        score = matches / len(data)
        if score > best_score:
            best_score = score
            print(f"  Millor: {score*100:.1f}% -> ((T + {offset}) ^ H) & 0xF")

    # 4. Check with M: P = M ^ ((T + Offset) & 0xF)
    print("Provant P = M ^ ((T + Offset) & 0xF) ...")
    for offset in range(256):
        matches = 0
        for r in data:
            if (r.m ^ ((r.t + offset) & 0xF)) == r.p:
                matches += 1
        score = matches / len(data)
        if score > best_score:
            best_score = score
            print(f"  Millor: {score*100:.1f}% -> M ^ ((T + {offset}) & 0xF)")

def main():
    data = load_data()
    solve_p(data)

if __name__ == "__main__":
    main()
