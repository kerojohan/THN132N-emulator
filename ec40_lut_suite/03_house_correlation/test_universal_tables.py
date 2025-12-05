#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Prueba de hipótesis: R12 es universal, independiente del house code
Basado en el hallazgo de que para 21.7°C, houses 151 y 255 tienen el mismo R12
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


def calculate_universal_tables(csv_path: str) -> Tuple[Dict, Dict]:
    """
    Calcula tablas M y P asumiendo que son universales (independientes del house code).
    Combina todos los datos de todos los houses.
    """
    
    print("="*80)
    print("CÁLCULO DE TABLAS UNIVERSALES M y P")
    print("="*80)
    print("\nHipótesis: R12 es el mismo para una temperatura dada,")
    print("           independientemente del house code.\n")
    
    # Recopilar todos los frames de todos los houses
    all_frames = []
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
                
                all_frames.append((temp_c, r12))
                frames_by_house[house].append((temp_c, r12))
            except Exception:
                continue
    
    print(f"Total de tramas combinadas: {len(all_frames)}")
    print(f"Houses: {sorted(frames_by_house.keys())}")
    
    # Calcular tablas con todos los datos combinados
    P_table = {d: 0x000 for d in range(10)}
    
    for iteration in range(10):
        M_candidates = defaultdict(Counter)
        
        for temp_c, r12 in all_frames:
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
        
        for temp_c, r12 in all_frames:
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
            print(f"Convergió en iteración {iteration + 1}")
            break
        
        P_table = new_P_table
    
    # Mostrar tablas
    print("\n" + "-"*80)
    print("TABLAS UNIVERSALES CALCULADAS:")
    print("-"*80)
    
    print("\nTabla P (décimas 0-9):")
    p_vals = [f"0x{P_table[d]:03X}" for d in range(10)]
    print(f"  {p_vals}")
    
    print(f"\nTabla M ({len(M_table)} temperaturas):")
    temps_sorted = sorted(M_table.keys())
    for i in range(0, len(temps_sorted), 5):
        temp_range = temps_sorted[i:i+5]
        m_vals = [f"{t}°C:0x{M_table[t]:03X}" for t in temp_range]
        print(f"  {', '.join(m_vals)}")
    
    # Verificar precisión global
    print("\n" + "-"*80)
    print("VERIFICACIÓN:")
    print("-"*80)
    
    correct = 0
    total = 0
    for temp_c, r12_obs in all_frames:
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
    print(f"\nPrecisión global: {accuracy:.2f}% ({correct}/{total})")
    
    # Verificar precisión por house
    print("\nPrecisión por house code:")
    for house in sorted(frames_by_house.keys()):
        correct_h = 0
        total_h = 0
        
        for temp_c, r12_obs in frames_by_house[house]:
            try:
                e, d = temp_to_e_d(temp_c)
            except ValueError:
                continue
            
            if e in M_table and d in P_table:
                r12_calc = M_table[e] ^ P_table[d]
                if r12_calc == r12_obs:
                    correct_h += 1
                total_h += 1
        
        acc_h = 100 * correct_h / total_h if total_h > 0 else 0
        print(f"  House {house:3d} (0x{house:02X}): {acc_h:5.2f}% ({correct_h}/{total_h})")
    
    # Analizar errores
    print("\n" + "-"*80)
    print("ANÁLISIS DE ERRORES:")
    print("-"*80)
    
    errors_by_temp = defaultdict(list)
    
    for temp_c, r12_obs in all_frames:
        try:
            e, d = temp_to_e_d(temp_c)
        except ValueError:
            continue
        
        if e in M_table and d in P_table:
            r12_calc = M_table[e] ^ P_table[d]
            if r12_calc != r12_obs:
                errors_by_temp[temp_c].append((r12_obs, r12_calc))
    
    if errors_by_temp:
        print(f"\nTemperaturas con errores: {len(errors_by_temp)}")
        print("Muestra de errores:")
        for i, (temp, errors) in enumerate(sorted(errors_by_temp.items())[:10]):
            print(f"  {temp}°C: {len(errors)} errores")
            for r12_obs, r12_calc in errors[:3]:
                diff = r12_obs ^ r12_calc
                print(f"    Obs=0x{r12_obs:03X}, Calc=0x{r12_calc:03X}, Diff=0x{diff:03X}")
    else:
        print("\n✓ ¡No hay errores! Las tablas universales funcionan perfectamente.")
    
    return M_table, P_table


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        csv_path = "ec40_live.csv"
        print(f"Usando archivo por defecto: {csv_path}\n")
    else:
        csv_path = sys.argv[1]
    
    M_table, P_table = calculate_universal_tables(csv_path)
    
    # Guardar resultados
    print("\n" + "="*80)
    print("GUARDANDO RESULTADOS...")
    print("="*80)
    
    with open("tablas_universales_live.txt", "w") as f:
        f.write("TABLAS UNIVERSALES M y P (calculadas desde ec40_live.csv)\n")
        f.write("="*80 + "\n\n")
        
        f.write("Tabla P:\n")
        f.write(f"P_TABLE = {[P_table[d] for d in range(10)]}\n\n")
        
        f.write("Tabla M:\n")
        f.write("M_TABLE = {\n")
        for temp in sorted(M_table.keys()):
            f.write(f"    {temp}: 0x{M_table[temp]:03X},\n")
        f.write("}\n")
    
    print("✓ Resultados guardados en 'tablas_universales_live.txt'")
