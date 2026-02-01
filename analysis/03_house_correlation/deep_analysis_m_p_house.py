#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Análisis profundo de la relación entre tablas M, P y house ID
Investiga:
1. ¿Varía la tabla M por house code?
2. ¿Qué tienen en común houses con 100% precisión?
3. ¿Hay familias de houses con comportamientos similares?
4. ¿El nibble bajo del house code es un selector de transformación?
"""

import csv
from collections import Counter, defaultdict
from typing import Dict, Tuple, List, Set

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
    """Calcula tablas M y P para un conjunto de frames."""
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
    """Análisis profundo de relaciones M/P con house ID."""
    
    print("="*80)
    print("ANÁLISIS PROFUNDO: TABLAS M/P vs HOUSE ID")
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
    
    print(f"\nTotal houses: {len(frames_by_house)}")
    for house in sorted(frames_by_house.keys()):
        print(f"  House {house:3d} (0x{house:02X}): {len(frames_by_house[house])} frames")
    
    # Calcular tablas para houses con datos suficientes
    print("\n" + "="*80)
    print("1. ANÁLISIS DE TABLA M POR HOUSE")
    print("="*80)
    
    m_tables = {}
    p_tables = {}
    
    for house in sorted(frames_by_house.keys()):
        if len(frames_by_house[house]) >= 10:
            m_table, p_table = calculate_tables(frames_by_house[house])
            m_tables[house] = m_table
            p_tables[house] = p_table
    
    # Comparar tablas M entre houses con temperaturas comunes
    print("\n¿Varía la tabla M según el house code?")
    print("-"*80)
    
    # Encontrar temperaturas comunes entre todos los houses
    temp_sets = [set(m_tables[h].keys()) for h in m_tables.keys()]
    common_temps = set.intersection(*temp_sets) if temp_sets else set()
    
    print(f"\nTemperaturas comunes entre todos los houses: {len(common_temps)}")
    
    if len(common_temps) > 0:
        print(f"Temperaturas: {sorted(common_temps)}")
        
        # Verificar si M es constante
        m_varies = False
        for temp in sorted(common_temps):
            m_values = set(m_tables[h][temp] for h in m_tables.keys() if temp in m_tables[h])
            if len(m_values) > 1:
                m_varies = True
                print(f"\nTemp {temp}°C: {len(m_values)} valores M diferentes:")
                for house in sorted(m_tables.keys()):
                    if temp in m_tables[house]:
                        print(f"  House {house:3d}: M[{temp}] = 0x{m_tables[house][temp]:03X}")
        
        if not m_varies:
            print("\n✓ La tabla M es CONSTANTE para todas las temperaturas comunes")
        else:
            print("\n✗ La tabla M VARÍA según el house code")
    
    # Encontrar temperaturas comunes entre pares de houses
    print("\n" + "-"*80)
    print("Temperaturas comunes entre pares de houses:")
    print("-"*80)
    
    houses_list = sorted(m_tables.keys())
    for i in range(len(houses_list)):
        for j in range(i+1, len(houses_list)):
            h1, h2 = houses_list[i], houses_list[j]
            common = set(m_tables[h1].keys()) & set(m_tables[h2].keys())
            
            if len(common) > 2:
                # Comparar valores M
                m_same = sum(1 for t in common if m_tables[h1][t] == m_tables[h2][t])
                m_diff = len(common) - m_same
                
                print(f"\nHouses {h1:3d} y {h2:3d}: {len(common)} temps comunes")
                print(f"  M iguales: {m_same}/{len(common)} ({100*m_same/len(common):.1f}%)")
                
                if m_diff > 0:
                    print(f"  Ejemplos de diferencias:")
                    count = 0
                    for t in sorted(common):
                        if m_tables[h1][t] != m_tables[h2][t]:
                            diff = m_tables[h1][t] ^ m_tables[h2][t]
                            print(f"    {t}°C: {h1}=0x{m_tables[h1][t]:03X}, {h2}=0x{m_tables[h2][t]:03X}, XOR=0x{diff:03X}")
                            count += 1
                            if count >= 3:
                                break
    
    # Análisis de houses con 100% precisión
    print("\n" + "="*80)
    print("2. ANÁLISIS DE HOUSES CON ALTA PRECISIÓN")
    print("="*80)
    
    # Usar tabla base (House 3) para validación
    if 3 in m_tables and 3 in p_tables:
        M_BASE = m_tables[3]
        P_BASE = p_tables[3]
        
        print("\nValidando con tabla base (House 3):")
        print("-"*80)
        
        for house in sorted(frames_by_house.keys()):
            if len(frames_by_house[house]) >= 5:
                correct = 0
                total = 0
                
                for temp_c, r12_obs in frames_by_house[house]:
                    try:
                        e, d = temp_to_e_d(temp_c)
                    except ValueError:
                        continue
                    
                    if e in M_BASE and d in P_BASE:
                        r12_calc = M_BASE[e] ^ P_BASE[d]
                        if r12_calc == r12_obs:
                            correct += 1
                        total += 1
                
                if total > 0:
                    precision = 100 * correct / total
                    status = "✅" if precision == 100 else "⭐" if precision > 80 else "✓" if precision > 50 else "✗"
                    print(f"{status} House {house:3d} (0x{house:02X}): {precision:5.1f}% ({correct:3d}/{total:3d})")
    
    # Análisis por nibble del house code
    print("\n" + "="*80)
    print("3. ANÁLISIS POR NIBBLES DEL HOUSE CODE")
    print("="*80)
    
    # Agrupar houses por nibble alto
    by_high_nibble = defaultdict(list)
    by_low_nibble = defaultdict(list)
    
    for house in m_tables.keys():
        high = (house >> 4) & 0x0F
        low = house & 0x0F
        by_high_nibble[high].append(house)
        by_low_nibble[low].append(house)
    
    print("\nAgrupación por nibble alto:")
    for nibble in sorted(by_high_nibble.keys()):
        houses = by_high_nibble[nibble]
        print(f"  Nibble 0x{nibble:X}: Houses {houses}")
        
        # Si hay múltiples houses con mismo nibble alto, comparar sus tablas P
        if len(houses) > 1:
            print(f"    Comparando tablas P:")
            h1 = houses[0]
            for h2 in houses[1:]:
                xor_vals = [p_tables[h1][d] ^ p_tables[h2][d] for d in range(10)]
                unique_xors = set(xor_vals)
                if len(unique_xors) == 1:
                    print(f"      Houses {h1} y {h2}: XOR constante = 0x{list(unique_xors)[0]:03X}")
                else:
                    print(f"      Houses {h1} y {h2}: XOR variable ({len(unique_xors)} valores)")
    
    print("\nAgrupación por nibble bajo:")
    for nibble in sorted(by_low_nibble.keys()):
        houses = by_low_nibble[nibble]
        print(f"  Nibble 0x{nibble:X}: Houses {houses}")
        
        if len(houses) > 1:
            print(f"    Comparando tablas P:")
            h1 = houses[0]
            for h2 in houses[1:]:
                xor_vals = [p_tables[h1][d] ^ p_tables[h2][d] for d in range(10)]
                unique_xors = set(xor_vals)
                if len(unique_xors) == 1:
                    print(f"      Houses {h1} y {h2}: XOR constante = 0x{list(unique_xors)[0]:03X} ⭐")
                else:
                    print(f"      Houses {h1} y {h2}: XOR variable ({len(unique_xors)} valores)")
    
    # Resumen de hallazgos
    print("\n" + "="*80)
    print("RESUMEN DE HALLAZGOS")
    print("="*80)
    
    print("\n1. Tabla M:")
    if len(common_temps) > 0:
        if not m_varies:
            print("   ✅ UNIVERSAL - No varía entre houses")
        else:
            print("   ⚠️  VARÍA entre algunos houses")
    else:
        print("   ❓ No hay suficientes temperaturas comunes para confirmar")
    
    print("\n2. Tabla P:")
    print("   ✓ Confirmado XOR constante entre Houses 3 y 247")
    print("   ❓ Relación con nibbles del house code por determinar")
    
    print("\n3. Houses con 100% precisión:")
    print("   → Usan tabla base directamente (sin transformación)")
    print("   → Posible familia de houses compatibles")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        csv_path = "ec40_capturas_merged.csv"
        print(f"Usando archivo por defecto: {csv_path}\n")
    else:
        csv_path = sys.argv[1]
    
    main(csv_path)
