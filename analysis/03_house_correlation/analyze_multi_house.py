#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Análisis de múltiples house IDs en ec40_live.csv
Busca correlaciones entre las tablas M y P de diferentes sensores
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


def calculate_tables_for_house(frames: List[Tuple[float, int]], house_id: int) -> Tuple[Dict, Dict]:
    """
    Calcula las tablas P y M para un house code dado.
    
    Args:
        frames: Lista de tuplas (temperatura, r12)
        house_id: ID del house
    
    Returns:
        (M_table, P_table)
    """
    print(f"\nCalculando tablas para House {house_id} con {len(frames)} tramas...")
    
    # Inicializar P con ceros
    P_table = {d: 0x000 for d in range(10)}
    
    # Iterar hasta convergencia
    for iteration in range(10):
        # Calcular M usando P actual
        M_candidates = defaultdict(Counter)
        
        for temp_c, r12 in frames:
            try:
                e, d = temp_to_e_d(temp_c)
            except ValueError:
                continue
            
            m_val = r12 ^ P_table[d]
            M_candidates[e][m_val] += 1
        
        # Elegir M más frecuente para cada temperatura
        M_table = {}
        for e, counter in M_candidates.items():
            if len(counter) > 0:
                val, cnt = counter.most_common(1)[0]
                M_table[e] = val
        
        # Calcular P usando M
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
        
        # Actualizar P
        new_P_table = {}
        for d in range(10):
            if d in P_candidates and len(P_candidates[d]) > 0:
                val, cnt = P_candidates[d].most_common(1)[0]
                new_P_table[d] = val
            else:
                new_P_table[d] = P_table[d]
        
        # Verificar convergencia
        if new_P_table == P_table:
            print(f"  Convergió en iteración {iteration + 1}")
            break
        
        P_table = new_P_table
    
    # Verificar precisión
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
    
    accuracy = 100 * correct / total if total > 0 else 0
    print(f"  Precisión: {accuracy:.2f}% ({correct}/{total})")
    
    return M_table, P_table


def compare_p_tables(p_tables: Dict[int, Dict]) -> None:
    """
    Compara las tablas P de diferentes house IDs buscando patrones.
    """
    print("\n" + "="*80)
    print("COMPARACIÓN DE TABLAS P")
    print("="*80)
    
    house_ids = sorted(p_tables.keys())
    
    # Mostrar todas las tablas P
    print("\nTablas P completas:")
    for hid in house_ids:
        p_vals = [f"0x{p_tables[hid][d]:03X}" for d in range(10)]
        print(f"House {hid:3d} (0x{hid:02X}): {p_vals}")
    
    # Comparar pares de tablas buscando XOR constante
    print("\n" + "-"*80)
    print("Análisis de transformaciones XOR entre tablas P:")
    print("-"*80)
    
    for i, h1 in enumerate(house_ids):
        for h2 in house_ids[i+1:]:
            # Calcular XOR entre las dos tablas
            xor_values = set()
            for d in range(10):
                if p_tables[h1][d] != 0 and p_tables[h2][d] != 0:
                    xor_val = p_tables[h1][d] ^ p_tables[h2][d]
                    xor_values.add(xor_val)
            
            if len(xor_values) == 1:
                xor_constant = list(xor_values)[0]
                print(f"✓ House {h1} vs {h2}: XOR constante = 0x{xor_constant:03X}")
                
                # Verificar si este XOR está relacionado con los house codes
                house_xor = h1 ^ h2
                print(f"  → house_code XOR: {h1} ^ {h2} = 0x{house_xor:02X}")
            elif len(xor_values) > 1 and len(xor_values) <= 3:
                print(f"~ House {h1} vs {h2}: XOR casi constante con {len(xor_values)} valores: {[f'0x{x:03X}' for x in xor_values]}")
            else:
                print(f"✗ House {h1} vs {h2}: Sin patrón XOR claro ({len(xor_values)} valores diferentes)")


def compare_m_tables(m_tables: Dict[int, Dict]) -> None:
    """
    Compara las tablas M de diferentes house IDs.
    """
    print("\n" + "="*80)
    print("COMPARACIÓN DE TABLAS M")
    print("="*80)
    
    house_ids = sorted(m_tables.keys())
    
    # Encontrar temperaturas comunes
    common_temps = set(m_tables[house_ids[0]].keys())
    for hid in house_ids[1:]:
        common_temps &= set(m_tables[hid].keys())
    
    common_temps = sorted(common_temps)
    
    print(f"\nTemperaturas comunes entre todos los house IDs: {len(common_temps)}")
    print(f"Rango: {min(common_temps)}°C a {max(common_temps)}°C")
    
    if len(common_temps) > 0:
        print("\nMuestra de valores M para temperaturas comunes:")
        sample_temps = common_temps[::max(1, len(common_temps)//10)][:10]
        
        for temp in sample_temps:
            print(f"\nTemp {temp:3d}°C:")
            for hid in house_ids:
                print(f"  House {hid:3d}: 0x{m_tables[hid][temp]:03X}")
        
        # Buscar si M es constante entre houses
        print("\n" + "-"*80)
        print("Verificando si M es universal (independiente del house code):")
        print("-"*80)
        
        all_same = True
        for temp in common_temps:
            values = set(m_tables[hid][temp] for hid in house_ids)
            if len(values) > 1:
                all_same = False
                print(f"Temp {temp:3d}°C: {len(values)} valores diferentes: {[f'0x{v:03X}' for v in values]}")
        
        if all_same:
            print("✓ ¡La tabla M parece ser UNIVERSAL! (igual para todos los house codes)")
        else:
            print("✗ La tabla M varía según el house code")


def main(csv_path: str):
    """Función principal."""
    print("="*80)
    print("ANÁLISIS DE CORRELACIÓN ENTRE HOUSE IDs")
    print("="*80)
    
    # Leer CSV y agrupar por house ID
    frames_by_house = defaultdict(list)
    
    with open(csv_path, newline='') as f:
        reader = csv.reader(f)
        first = True
        
        for row in reader:
            if not row or len(row) < 8:
                continue
            
            # Saltar header
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
                
                # Extraer R12
                msg = bytes.fromhex(ec40_hex)
                b3_low = msg[3] & 0x0F
                b7 = msg[7]
                r12 = ((b3_low << 8) | b7) & 0xFFF
                
                frames_by_house[house].append((temp_c, r12))
            except Exception as e:
                continue
    
    print(f"\nHouse IDs encontrados: {sorted(frames_by_house.keys())}")
    print(f"Total de house IDs: {len(frames_by_house)}")
    
    for hid in sorted(frames_by_house.keys()):
        print(f"  House {hid:3d} (0x{hid:02X}): {len(frames_by_house[hid])} tramas")
    
    # Calcular tablas para cada house
    m_tables = {}
    p_tables = {}
    
    for hid in sorted(frames_by_house.keys()):
        m_table, p_table = calculate_tables_for_house(frames_by_house[hid], hid)
        m_tables[hid] = m_table
        p_tables[hid] = p_table
    
    # Comparar tablas
    compare_p_tables(p_tables)
    compare_m_tables(m_tables)
    
    # Resumen final
    print("\n" + "="*80)
    print("RESUMEN Y CONCLUSIONES")
    print("="*80)
    print("\nPara poder hacer un análisis completo, necesitamos:")
    print("1. Más tramas con temperaturas idénticas en diferentes house IDs")
    print("2. Capturas que cubran el mismo rango de temperaturas")
    print("3. Verificar si el nibble alto de byte3 contiene información del house code")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        csv_path = "ec40_live.csv"
        print(f"Usando archivo por defecto: {csv_path}")
    else:
        csv_path = sys.argv[1]
    
    main(csv_path)
