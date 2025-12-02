#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Análisis corregido: R12 incluye información del house code.

El byte 3 del mensaje EC40 tiene:
- Nibble alto (4 bits): relacionado con house code
- Nibble bajo (4 bits): parte alta de R12

Por lo tanto, R12 = ((byte3 & 0x0F) << 8) | byte7
Y el cálculo debe ser: R12 = M[e] ^ P[d] ^ H[house]

donde H[house] es una función del house code.
"""

import csv
from collections import Counter, defaultdict
from typing import Dict, Tuple, List

KNOWN_PREAMBLE = "555555559995a5a6aa6a"


def temp_to_e_d(temp_c: float) -> Tuple[int, int]:
    """Descompone temperatura en parte entera e y décima d."""
    e = int(temp_c)
    t10 = int(round(abs(temp_c * 10)))
    d = t10 - abs(e) * 10
    if d < 0 or d > 9:
        raise ValueError(f"décima fuera de rango para temp={temp_c}: d={d}")
    return e, d


def analyze_house_code_relationship(csv_path: str):
    """Analiza la relación entre house code y b3_high."""
    
    house_to_b3high = {}
    
    with open(csv_path, newline='') as f:
        reader = csv.reader(f)
        first = True
        
        for row in reader:
            if not row:
                continue
            
            if first:
                first = False
                try:
                    float(row[3])
                except Exception:
                    continue
            
            raw168_hex = row[1].strip().lower()
            if not raw168_hex.startswith(KNOWN_PREAMBLE.lower()):
                continue
            
            ec40_hex = row[2]
            house = int(row[5].strip())
            
            msg = bytes.fromhex(ec40_hex)
            b3_high = (msg[3] >> 4) & 0x0F
            
            if house not in house_to_b3high:
                house_to_b3high[house] = b3_high
            elif house_to_b3high[house] != b3_high:
                print(f"⚠️  House {house} tiene múltiples b3_high: {house_to_b3high[house]:X} y {b3_high:X}")
    
    print("Relación House Code → b3_high:")
    print("="*60)
    for house in sorted(house_to_b3high.keys()):
        b3h = house_to_b3high[house]
        print(f"House {house:3d} (0x{house:02X}) → b3_high = 0x{b3h:X}")
    
    # Intentar encontrar la relación
    print("\nBuscando patrón...")
    for house in sorted(house_to_b3high.keys()):
        b3h = house_to_b3high[house]
        
        # Probar diferentes operaciones
        xor_result = house ^ b3h
        print(f"House {house:3d}: b3_high={b3h:X}, house^b3_high=0x{xor_result:02X}")
    
    return house_to_b3high


def recalculate_with_house_offset(csv_path: str):
    """
    Recalcula las tablas M y P considerando que cada house code
    tiene un offset en R12.
    """
    
    # Primero, identificar el offset por house code
    print("\n" + "="*60)
    print("Analizando offset por house code...")
    print("="*60)
    
    frames_by_house = defaultdict(list)
    
    with open(csv_path, newline='') as f:
        reader = csv.reader(f)
        first = True
        
        for row in reader:
            if not row:
                continue
            
            if first:
                first = False
                try:
                    float(row[3])
                except Exception:
                    continue
            
            raw168_hex = row[1].strip().lower()
            if not raw168_hex.startswith(KNOWN_PREAMBLE.lower()):
                continue
            
            try:
                temp_c = float(row[3].strip())
                house = int(row[5].strip())
                ec40_hex = row[2]
                
                msg = bytes.fromhex(ec40_hex)
                b3_low = msg[3] & 0x0F
                b7 = msg[7]
                r12 = ((b3_low << 8) | b7) & 0xFFF
                
                frames_by_house[house].append((temp_c, r12))
            except Exception:
                continue
    
    # Para cada house, calcular las tablas P y M
    print("\nTablas P y M por house code:")
    print("="*60)
    
    for house in sorted(frames_by_house.keys(), key=lambda x: len(frames_by_house[x]), reverse=True)[:3]:
        frames = frames_by_house[house]
        print(f"\nHouse {house}: {len(frames)} tramas")
        
        # Calcular P iterativamente
        P_table = {d: 0x000 for d in range(10)}
        
        for iteration in range(5):
            M_candidates = defaultdict(Counter)
            
            for temp_c, r12 in frames:
                try:
                    e, d = temp_to_e_d(temp_c)
                except ValueError:
                    continue
                
                m_val = r12 ^ P_table[d]
                M_candidates[e][m_val] += 1
            
            M_table = {}
            for e, counter in M_candidates.items():
                val, cnt = counter.most_common(1)[0]
                M_table[e] = val
            
            P_candidates = defaultdict(Counter)
            
            for temp_c, r12 in frames:
                try:
                    e, d = temp_to_e_d(temp_c)
                except ValueError:
                    continue
                
                if e not in M_table:
                    continue
                
                p_val = r12 ^ M_table[e]
                P_candidates[d][p_val] += 1
            
            new_P_table = {}
            for d in range(10):
                if d in P_candidates and len(P_candidates[d]) > 0:
                    val, cnt = P_candidates[d].most_common(1)[0]
                    new_P_table[d] = val
                else:
                    new_P_table[d] = P_table[d]
            
            if new_P_table == P_table:
                break
            
            P_table = new_P_table
        
        # Mostrar tabla P
        print("  Tabla P:", [f"0x{P_table[d]:03X}" for d in range(10)])
        
        # Verificar
        correct = 0
        total = 0
        for temp_c, r12_obs in frames:
            try:
                e, d = temp_to_e_d(temp_c)
            except ValueError:
                continue
            
            if e in M_table and d in P_table:
                r12_calc = M_table[e] ^ P_table[d]
                if r12_calc == r12_obs:
                    correct += 1
                total += 1
        
        if total > 0:
            print(f"  Precisión: {100*correct/total:.2f}% ({correct}/{total})")


def main(csv_path: str):
    print("Análisis de la relación entre House Code y R12")
    print("="*60)
    
    house_to_b3high = analyze_house_code_relationship(csv_path)
    recalculate_with_house_offset(csv_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python3 analyze_house_r12.py ec40_capturas_merged.csv")
        sys.exit(1)
    
    main(sys.argv[1])
