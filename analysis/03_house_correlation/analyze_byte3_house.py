#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Análisis detallado del nibble alto de byte3 y su relación con R12
Este script examina si R12 incluye información del house code
"""

import csv
from collections import defaultdict
from typing import Dict, Tuple

KNOWN_PREAMBLE = "555555559995a5a6aa6a"


def temp_to_e_d(temp_c: float) -> Tuple[int, int]:
    """Descompone temperatura en parte entera e y décima d."""
    e = int(temp_c)
    t10 = int(round(abs(temp_c * 10)))
    d = t10 - abs(e) * 10
    if d < 0 or d > 9:
        raise ValueError(f"décima fuera de rango para temp={temp_c}: d={d}")
    return e, d


def main(csv_path: str):
    """Analiza la relación entre house code y byte3."""
    
    print("="*80)
    print("ANÁLISIS DEL BYTE3 Y SU RELACIÓN CON HOUSE CODE")
    print("="*80)
    
    # Agrupar datos por house
    data_by_house = defaultdict(list)
    
    with open(csv_path, newline='') as f:
        reader = csv.reader(f)
        first = True
        
        for row in reader:
            if not row or len(row) < 8:
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
                byte3 = msg[3]
                b3_high = (byte3 >> 4) & 0x0F
                b3_low = byte3 & 0x0F
                b7 = msg[7]
                r12 = ((b3_low << 8) | b7) & 0xFFF
                
                data_by_house[house].append({
                    'temp': temp_c,
                    'byte3': byte3,
                    'b3_high': b3_high,
                    'b3_low': b3_low,
                    'b7': b7,
                    'r12': r12
                })
            except Exception as e:
                continue
    
    # Analizar relación house → b3_high
    print("\n1. RELACIÓN HOUSE CODE → BYTE3 (nibble alto)")
    print("-"*80)
    
    for house in sorted(data_by_house.keys()):
        frames = data_by_house[house]
        b3_high_values = set(f['b3_high'] for f in frames)
        
        if len(b3_high_values) == 1:
            b3h = list(b3_high_values)[0]
            print(f"House {house:3d} (0x{house:02X}) → b3_high = 0x{b3h:X} (constante)")
            
            # Analizar la relación
            house_high_nibble = (house >> 4) & 0x0F
            house_low_nibble = house & 0x0F
            
            print(f"  House nibble alto: 0x{house_high_nibble:X}")
            print(f"  House nibble bajo: 0x{house_low_nibble:X}")
            
            if b3h == house_high_nibble:
                print(f"  ✓ b3_high == house nibble alto")
            elif b3h == house_low_nibble:
                print(f"  ✓ b3_high == house nibble bajo")
            else:
                xor_high = b3h ^ house_high_nibble
                xor_low = b3h ^ house_low_nibble
                print(f"  b3_high XOR house_high = 0x{xor_high:X}")
                print(f"  b3_high XOR house_low = 0x{xor_low:X}")
        else:
            print(f"House {house:3d} (0x{house:02X}) → b3_high VARIABLE: {[f'0x{x:X}' for x in b3_high_values]}")
    
    # Buscar temperaturas idénticas entre diferentes houses
    print("\n\n2. ANÁLISIS DE TEMPERATURAS IDÉNTICAS ENTRE HOUSES")
    print("-"*80)
    
    # Agrupar por temperatura
    temp_data = defaultdict(list)
    for house in sorted(data_by_house.keys()):
        for frame in data_by_house[house]:
            temp_data[frame['temp']].append((house, frame['r12'], frame['b3_high'], frame['b7']))
    
    # Mostrar temperaturas con múltiples houses
    print("\nTemperaturas capturadas con múltiples house IDs:")
    for temp in sorted(temp_data.keys()):
        houses_with_temp = set(h for h, _, _, _ in temp_data[temp])
        if len(houses_with_temp) >= 2:
            print(f"\n  Temperatura: {temp}°C ({len(houses_with_temp)} houses)")
            for house, r12, b3h, b7 in sorted(temp_data[temp]):
                print(f"    House {house:3d} (0x{house:02X}): R12=0x{r12:03X}, b3_high=0x{b3h:X}, b7=0x{b7:02X}")
            
            # Comparar R12 entre houses
            r12_values = [r12 for _, r12, _, _ in temp_data[temp]]
            if len(set(r12_values)) == 1:
                print(f"    → ✓ Mismo R12 para todos los houses!")
            else:
                print(f"    → ✗ R12 diferentes:")
                # Analizar diferencias
                r12_list = list(temp_data[temp])
                for i in range(len(r12_list)):
                    for j in range(i+1, len(r12_list)):
                        h1, r12_1, _, _ = r12_list[i]
                        h2, r12_2, _, _ = r12_list[j]
                        r12_xor = r12_1 ^ r12_2
                        house_xor = h1 ^ h2
                        print(f"      House {h1} vs {h2}: R12 XOR = 0x{r12_xor:03X}, House XOR = 0x{house_xor:02X}")
    
    # Análisis de rango de temperaturas por house
    print("\n\n3. COBERTURA DE TEMPERATURAS POR HOUSE ID")
    print("-"*80)
    
    for house in sorted(data_by_house.keys()):
        temps = [f['temp'] for f in data_by_house[house]]
        print(f"House {house:3d} (0x{house:02X}): {min(temps):.1f}°C - {max(temps):.1f}°C ({len(temps)} muestras)")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        csv_path = "ec40_live.csv"
        print(f"Usando archivo por defecto: {csv_path}\n")
    else:
        csv_path = sys.argv[1]
    
    main(csv_path)
