#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Análisis CORRECTO: Las tablas M y P son universales.

El byte 3 codifica:
- Nibble alto: (house_code >> 4) & 0x0F
- Nibble bajo: (R12 >> 8) & 0x0F

Por lo tanto, para calcular R12 solo necesitamos M[e] y P[d],
SIN depender del house code.
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


def load_all_frames(csv_path: str) -> List[Tuple[float, int, int, str]]:
    """
    Carga todas las tramas válidas.
    Returns: list[(temp_c, r12, house, raw168)]
    """
    frames = []
    skipped = 0
    
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
                skipped += 1
                continue
            
            try:
                temp_c = float(row[3].strip())
                house = int(row[5].strip())
                ec40_hex = row[2]
                
                msg = bytes.fromhex(ec40_hex)
                b3_low = msg[3] & 0x0F
                b7 = msg[7]
                r12 = ((b3_low << 8) | b7) & 0xFFF
                
                frames.append((temp_c, r12, house, raw168_hex))
            except Exception:
                continue
    
    print(f"Tramas válidas: {len(frames)}")
    print(f"Tramas descartadas: {skipped}\n")
    
    return frames


def calculate_universal_tables(frames: List[Tuple[float, int, int, str]], iterations: int = 10) -> Tuple[Dict[int, int], Dict[int, int]]:
    """
    Calcula tablas P y M universales usando TODAS las tramas.
    """
    # Inicializar P[d] = 0
    P_table = {d: 0x000 for d in range(10)}
    
    for iteration in range(iterations):
        # Calcular M[e] usando P[d] actual
        M_candidates = defaultdict(Counter)
        
        for temp_c, r12, house, _ in frames:
            try:
                e, d = temp_to_e_d(temp_c)
            except ValueError:
                continue
            
            m_val = r12 ^ P_table[d]
            M_candidates[e][m_val] += 1
        
        # Elegir M[e] más frecuente
        M_table = {}
        for e, counter in M_candidates.items():
            val, cnt = counter.most_common(1)[0]
            M_table[e] = val
        
        # Recalcular P[d] usando M[e]
        P_candidates = defaultdict(Counter)
        
        for temp_c, r12, house, _ in frames:
            try:
                e, d = temp_to_e_d(temp_c)
            except ValueError:
                continue
            
            if e not in M_table:
                continue
            
            p_val = r12 ^ M_table[e]
            P_candidates[d][p_val] += 1
        
        # Actualizar P[d]
        new_P_table = {}
        for d in range(10):
            if d in P_candidates and len(P_candidates[d]) > 0:
                val, cnt = P_candidates[d].most_common(1)[0]
                new_P_table[d] = val
            else:
                new_P_table[d] = P_table[d]
        
        # Verificar convergencia
        if new_P_table == P_table:
            print(f"Convergencia en iteración {iteration + 1}")
            break
        
        P_table = new_P_table
    
    # Recalcular M final
    M_candidates = defaultdict(Counter)
    for temp_c, r12, house, _ in frames:
        try:
            e, d = temp_to_e_d(temp_c)
        except ValueError:
            continue
        if d not in P_table:
            continue
        m_val = r12 ^ P_table[d]
        M_candidates[e][m_val] += 1
    
    M_table = {}
    for e, counter in M_candidates.items():
        val, cnt = counter.most_common(1)[0]
        M_table[e] = val
    
    return P_table, M_table


def verify_universal_tables(frames: List[Tuple[float, int, int, str]], 
                            M_table: Dict[int, int], 
                            P_table: Dict[int, int]):
    """Verifica las tablas universales."""
    
    correct_by_house = defaultdict(int)
    errors_by_house = defaultdict(int)
    error_examples = []
    
    for temp_c, r12_obs, house, _ in frames:
        try:
            e, d = temp_to_e_d(temp_c)
        except ValueError:
            continue
        
        if e not in M_table or d not in P_table:
            continue
        
        r12_calc = M_table[e] ^ P_table[d]
        
        if r12_calc == r12_obs:
            correct_by_house[house] += 1
        else:
            errors_by_house[house] += 1
            if len(error_examples) < 10:
                error_examples.append({
                    'temp': temp_c,
                    'house': house,
                    'e': e,
                    'd': d,
                    'r12_obs': r12_obs,
                    'r12_calc': r12_calc,
                    'M_e': M_table[e],
                    'P_d': P_table[d]
                })
    
    # Mostrar resultados
    print("\nVerificación por house code:")
    print("="*60)
    
    total_correct = 0
    total_errors = 0
    
    for house in sorted(set(list(correct_by_house.keys()) + list(errors_by_house.keys()))):
        correct = correct_by_house[house]
        errors = errors_by_house[house]
        total = correct + errors
        precision = 100 * correct / total if total > 0 else 0
        
        total_correct += correct
        total_errors += errors
        
        print(f"House {house:3d}: {precision:6.2f}% ({correct:4d}/{total:4d})")
    
    total = total_correct + total_errors
    overall_precision = 100 * total_correct / total if total > 0 else 0
    
    print(f"\n{'TOTAL':>8}: {overall_precision:6.2f}% ({total_correct:4d}/{total:4d})")
    
    if error_examples:
        print("\nPrimeros errores:")
        for i, err in enumerate(error_examples, 1):
            print(f"{i}. Temp={err['temp']:.1f}°C, House={err['house']}, e={err['e']}, d={err['d']}")
            print(f"   R12 obs=0x{err['r12_obs']:03X}, calc=0x{err['r12_calc']:03X}")
            print(f"   M[{err['e']}]=0x{err['M_e']:03X}, P[{err['d']}]=0x{err['P_d']:03X}")


def main(csv_path: str):
    print("Cálculo de Tablas M y P UNIVERSALES")
    print("="*60)
    print()
    
    # Cargar todas las tramas
    frames = load_all_frames(csv_path)
    
    # Calcular tablas universales
    print("Calculando tablas universales...")
    P_table, M_table = calculate_universal_tables(frames)
    
    print("\nTabla P[d]:")
    for d in range(10):
        print(f"  P[{d}] = 0x{P_table[d]:03X}")
    
    print(f"\nTabla M[e]: {len(M_table)} temperaturas")
    print("Primeras 10:")
    for i, e in enumerate(sorted(M_table.keys())[:10]):
        print(f"  M[{e:4d}] = 0x{M_table[e]:03X}")
    
    # Verificar
    verify_universal_tables(frames, M_table, P_table)
    
    # Guardar
    with open('tablas_M_P_universales.md', 'w') as f:
        f.write("# Tablas M y P Universales\n\n")
        f.write("## Tabla P[d] - Décimas\n\n")
        f.write("```python\n")
        f.write("P_TABLE = [\n")
        for d in range(10):
            f.write(f"    0x{P_table[d]:03X},  # P[{d}]\n")
        f.write("]\n")
        f.write("```\n\n")
        
        f.write("## Tabla M[e] - Temperaturas enteras\n\n")
        f.write("```python\n")
        f.write("M_TABLE = {\n")
        for e in sorted(M_table.keys()):
            f.write(f"    {e:4d}: 0x{M_table[e]:03X},\n")
        f.write("}\n")
        f.write("```\n")
    
    print("\n✅ Tablas guardadas en: tablas_M_P_universales.md")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python3 calc_universal_tables.py ec40_capturas_merged.csv")
        sys.exit(1)
    
    main(sys.argv[1])
