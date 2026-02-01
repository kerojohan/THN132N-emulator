#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Análisis de patrones XOR en tabla M entre different houses
Dado que M varía por house, buscar si hay transformación XOR como en P
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


def calculate_tables(frames: List[Tuple[float, int]]) -> Tuple[Dict, Dict]:
    """Calcula tablas M y P."""
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
    
    return M_table, P_table


def main(csv_path: str):
    """Busca patrones XOR en tabla M."""
    
    print("="*80)
    print("ANÁLISIS DE PATRONES XOR EN TABLA M")
    print("="*80)
    
    # Recopilar frames
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
    
    # Calcular tablas
    m_tables = {}
    p_tables = {}
    
    for house in sorted(frames_by_house.keys()):
        if len(frames_by_house[house]) >= 10:
            m_table, p_table = calculate_tables(frames_by_house[house])
            m_tables[house] = m_table
            p_tables[house] = p_table
    
    print(f"\nHouses analizados: {sorted(m_tables.keys())}")
    
    # Analizar XOR en tabla M entre pares de houses
    print("\n" + "="*80)
    print("PATRONES XOR EN TABLA M")
    print("="*80)
    
    houses = sorted(m_tables.keys())
    
    for i in range(len(houses)):
        for j in range(i+1, len(houses)):
            h1, h2 = houses[i], houses[j]
            
            # Encontrar temperaturas comunes
            common_temps = set(m_tables[h1].keys()) & set(m_tables[h2].keys())
            
            if len(common_temps) < 5:
                continue
            
            print(f"\n{'-'*80}")
            print(f"Houses {h1} ({len(m_tables[h1])} temps) vs {h2} ({len(m_tables[h2])} temps)")
            print(f"Temperaturas comunes: {len(common_temps)}")
            
            # Calcular XORs entre M
            xor_values = []
            for temp in sorted(common_temps):
                m1 = m_tables[h1][temp]
                m2 = m_tables[h2][temp]
                xor_val = m1 ^ m2
                xor_values.append(xor_val)
            
            unique_xors = set(xor_values)
            
            if len(unique_xors) == 1:
                xor_mask = list(unique_xors)[0]
                print(f"  ✓ XOR CONSTANTE = 0x{xor_mask:03X} en tabla M")
                print(f"    M_{h2}[t] = M_{h1}[t] ^ 0x{xor_mask:03X}")
            elif len(unique_xors) <= 3:
                print(f"  ~ XOR casi constante: {len(unique_xors)} valores")
                for xor_val in sorted(unique_xors):
                    count = xor_values.count(xor_val)
                    print(f"    0x{xor_val:03X}: {count}/{len(xor_values)} veces ({100*count/len(xor_values):.1f}%)")
            else:
                print(f"  ✗ Sin patrón XOR claro ({len(unique_xors)} valores diferentes)")
            
            # Mostrar ejemplos
            print(f"  Ejemplos:")
            for temp in sorted(common_temps)[:5]:
                m1 = m_tables[h1][temp]
                m2 = m_tables[h2][temp]
                xor_val = m1 ^ m2
                print(f"    {temp:3d}°C: M_{h1}=0x{m1:03X}, M_{h2}=0x{m2:03X}, XOR=0x{xor_val:03X}")
    
    # Comparar con patrones en tabla P
    print("\n" + "="*80)
    print("COMPARACIÓN: PATRONES XOR EN TABLA P vs TABLA M")
    print("="*80)
    
    for i in range(len(houses)):
        for j in range(i+1, len(houses)):
            h1, h2 = houses[i], houses[j]
            
            # XOR en tabla P
            p_xors = [p_tables[h1][d] ^ p_tables[h2][d] for d in range(10)]
            p_unique = set(p_xors)
            
            # XOR en tabla M
            common_temps = set(m_tables[h1].keys()) & set(m_tables[h2].keys())
            if len(common_temps) < 5:
                continue
            
            m_xors = [m_tables[h1][t] ^ m_tables[h2][t] for t in sorted(common_temps)]
            m_unique = set(m_xors)
            
            print(f"\nHouses {h1} vs {h2}:")
            
            if len(p_unique) == 1:
                print(f"  Tabla P: XOR constante = 0x{list(p_unique)[0]:03X}")
            else:
                print(f"  Tabla P: {len(p_unique)} valores XOR diferentes")
            
            if len(m_unique) == 1:
                print(f"  Tabla M: XOR constante = 0x{list(m_unique)[0]:03X}")
            else:
                print(f"  Tabla M: {len(m_unique)} valores XOR diferentes")
            
            # ¿Hay relación entre XORs de M y P?
            if len(p_unique) == 1 and len(m_unique) == 1:
                p_xor = list(p_unique)[0]
                m_xor = list(m_unique)[0]
                print(f"  → P_XOR = 0x{p_xor:03X}, M_XOR = 0x{m_xor:03X}")
                
                if p_xor == m_xor:
                    print(f"    ✓ ¡MISMO XOR para M y P!")
                else:
                    diff = p_xor ^ m_xor
                    print(f"    Diferencia: 0x{diff:03X}")
    
    # Conclusiones
    print("\n" + "="*80)
    print("CONCLUSIONES")
    print("="*80)
    
    print("\n1. Tabla M:")
    print("   → NO es universal")
    print("   → Varía según el house code")
    print("   → Buscar si hay transformación XOR como en tabla P")
    
    print("\n2. Tabla P:")
    print("   → XOR constante confirmado entre Houses 3 y 247 (0x075)")
    
    print("\n3. Relación M ↔ P:")
    print("   → Investigar si ambas tablas se transforman con mismo XOR")
    print("   → O si cada una tiene su propia transformación")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        csv_path = "ec40_capturas_merged.csv"
        print(f"Usando archivo por defecto: {csv_path}\n")
    else:
        csv_path = sys.argv[1]
    
    main(csv_path)
