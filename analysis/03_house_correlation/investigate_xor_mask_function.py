#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Investigación de la función general calculate_xor_mask(house_code)
Analiza todos los houses disponibles para encontrar el patrón de transformación
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


def calculate_p_table(frames: List[Tuple[float, int]]) -> Dict[int, int]:
    """Calcula la tabla P para un conjunto de frames."""
    P_table = {d: 0x000 for d in range(10)}
    
    for iteration in range(10):
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
            if len(counter) > 0:
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
    
    return P_table


def main(csv_path: str):
    """Analiza XOR masks entre todos los pares de houses."""
    
    print("="*80)
    print("INVESTIGACIÓN DE LA FUNCIÓN calculate_xor_mask(house_code)")
    print("="*80)
    
    # Recopilar frames por house
    frames_by_house = defaultdict(list)
    
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
                b3_low = msg[3] & 0x0F
                b7 = msg[7]
                r12 = ((b3_low << 8) | b7) & 0xFFF
                
                frames_by_house[house].append((temp_c, r12))
            except Exception:
                continue
    
    # Calcular tabla P para cada house con suficientes datos
    print(f"\n1. CALCULANDO TABLAS P")
    print("-"*80)
    
    p_tables = {}
    for house in sorted(frames_by_house.keys()):
        if len(frames_by_house[house]) >= 10:  # Mínimo 10 frames
            p_table = calculate_p_table(frames_by_house[house])
            p_tables[house] = p_table
            print(f"House {house:3d} (0x{house:02X}): {len(frames_by_house[house])} frames")
    
    # Tabla P de referencia (House 3)
    P_BASE = None
    if 3 in p_tables:
        P_BASE = p_tables[3]
        print(f"\n✓ Usando House 3 como tabla base de referencia")
    else:
        print(f"\n⚠ House 3 no disponible, usando primer house como referencia")
        P_BASE = p_tables[sorted(p_tables.keys())[0]]
    
    # Analizar XOR entre cada house y la tabla base
    print(f"\n2. ANÁLISIS DE XOR MASKS")
    print("-"*80)
    print(f"\nTabla base: {[f'0x{P_BASE[d]:03X}' for d in range(10)]}\n")
    
    xor_patterns = {}
    
    for house in sorted(p_tables.keys()):
        if house == 3:  # Skip la base
            continue
        
        p_table = p_tables[house]
        
        # Calcular XOR con la tabla base
        xor_values = []
        for d in range(10):
            xor_val = P_BASE[d] ^ p_table[d]
            xor_values.append(xor_val)
        
        unique_xors = set(xor_values)
        
        print(f"House {house:3d} (0x{house:02X}):")
        print(f"  Tabla P: {[f'0x{p_table[d]:03X}' for d in range(10)]}")
        
        if len(unique_xors) == 1:
            xor_mask = list(unique_xors)[0]
            print(f"  ✓ XOR constante = 0x{xor_mask:03X}")
            xor_patterns[house] = xor_mask
        elif len(unique_xors) <= 3:
            print(f"  ~ XOR casi constante: {[f'0x{x:03X}' for x in sorted(unique_xors)]}")
            xor_patterns[house] = None
        else:
            print(f"  ✗ Sin patrón XOR claro ({len(unique_xors)} valores)")
            xor_patterns[house] = None
        
        print()
    
    # Buscar correlación entre house code y XOR mask
    print(f"3. BÚSQUEDA DE PATRÓN")
    print("-"*80)
    
    print("\nHouses con XOR constante:")
    print(f"{'House':<8} {'Hex':<8} {'XOR Mask':<12} {'H^3':<8} {'H>>4':<8} {'H&0xF':<8}")
    print("-"*80)
    
    for house, xor_mask in sorted(xor_patterns.items()):
        if xor_mask is not None:
            h_xor_3 = house ^ 3
            h_high = (house >> 4) & 0x0F
            h_low = house & 0x0F
            
            
            print(f"{house:<8} 0x{house:02X} {'':<4} 0x{xor_mask:03X} {'':<6} 0x{h_xor_3:02X} {'':<3} 0x{h_high:X} {'':<5} 0x{h_low:X}")
            
            # Verificar si el XOR mask coincide con alguna operación simple
            if xor_mask == h_xor_3:
                print(f"  → XOR mask = house ^ 3")
            elif xor_mask == ((h_xor_3 << 4) | h_xor_3) & 0xFFF:
                print(f"  → XOR mask = (house^3) repetido en nibbles")
            elif xor_mask == 0x075:
                print(f"  → XOR mask fijo = 0x075")
    
    # Proponer función
    print(f"\n4. FUNCIÓN PROPUESTA")
    print("-"*80)
    
    if 247 in xor_patterns and xor_patterns[247] == 0x075:
        print("""
def calculate_xor_mask(house_code):
    \"\"\"
    Calcula el XOR mask para derivar la tabla P del house code dado.
    Basado en análisis empírico de capturas reales.
    \"\"\"
    # Tabla base es House 3
    if house_code == 3:
        return 0x000  # Sin transformación
    
    # Patrón confirmado para House 247
    elif house_code == 247:
        return 0x075
    
    # Para otros houses, intentar derivar del XOR con House 3
    else:
        # Por determinar - necesitamos más datos
        # Posibles patrones:
        # - XOR directo con 3: house_code ^ 3
        # - Función del nibble bajo
        # - Lookup table específica
        return None  # No confirmado aún
        """)
    
    print(f"\n5. RECOMENDACIONES")
    print("-"*80)
    print("\nPara completar la función:")
    print("1. Capturar más datos de houses con patrones no claros")
    print("2. Verificar si houses con mismo nibble alto comparten patrón")
    print("3. Analizar nibble bajo como posible selector de transformación")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        csv_path = "ec40_capturas_merged.csv"
        print(f"Usando archivo por defecto: {csv_path}\n")
    else:
        csv_path = sys.argv[1]
    
    main(csv_path)
