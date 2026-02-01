#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Recalcula las tablas M y P por sensor (house code).

Este script analiza las tramas capturadas separando por house code,
ya que cada sensor puede tener sus propias tablas M y P.
"""

import csv
import sys
from collections import Counter, defaultdict
from typing import Dict, Tuple, List

# Preámbulo conocido de Oregon Scientific v2.1 para THN132N
KNOWN_PREAMBLE = "555555559995a5a6aa6a"


def temp_to_e_d(temp_c: float) -> Tuple[int, int]:
    """Descompone temperatura en parte entera e y décima d."""
    e = int(temp_c)
    t10 = int(round(abs(temp_c * 10)))
    d = t10 - abs(e) * 10
    if d < 0 or d > 9:
        raise ValueError(f"décima fuera de rango para temp={temp_c}: d={d}")
    return e, d


def r12_from_ec40(ec40_hex: str) -> int:
    """Calcula R12 desde EC40 hex."""
    ec40_hex = ec40_hex.strip()
    if len(ec40_hex) < 16:
        raise ValueError(f"Trama EC40 demasiado corta: {ec40_hex}")
    msg = bytes.fromhex(ec40_hex)
    if len(msg) < 8:
        raise ValueError(f"EC40 no tiene 8 bytes: {ec40_hex}")
    b3_low = msg[3] & 0x0F
    b7 = msg[7]
    return ((b3_low << 8) | b7) & 0xFFF


def load_frames_by_sensor(csv_path: str) -> Dict[str, List[Tuple[float, int, str]]]:
    """
    Carga tramas agrupadas por house code.
    Returns: dict[house_code] -> list[(temp_c, r12, raw168)]
    """
    frames_by_sensor = defaultdict(list)
    skipped_count = 0
    
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
            
            # Filtrar por preámbulo
            if not raw168_hex.startswith(KNOWN_PREAMBLE.lower()):
                skipped_count += 1
                continue
            
            try:
                temp_c = float(row[3].strip())
                house = row[5].strip()
            except Exception:
                continue
            
            # Obtener R12
            r12 = None
            if len(row) >= 9 and row[8].strip().startswith("0x"):
                try:
                    r12 = int(row[8].strip(), 16) & 0xFFF
                except Exception:
                    r12 = None
            
            if r12 is None:
                ec40_hex = row[2]
                try:
                    r12 = r12_from_ec40(ec40_hex)
                except Exception:
                    continue
            
            frames_by_sensor[house].append((temp_c, r12, raw168_hex))
    
    print(f"Tramas descartadas (sin preámbulo correcto): {skipped_count}\n")
    print("Tramas por sensor (house code):")
    for house in sorted(frames_by_sensor.keys(), key=lambda x: len(frames_by_sensor[x]), reverse=True):
        print(f"  House {house}: {len(frames_by_sensor[house])} tramas")
    
    return frames_by_sensor


def calculate_tables_for_sensor(frames: List[Tuple[float, int, str]], iterations: int = 5) -> Tuple[Dict[int, int], Dict[int, int]]:
    """
    Calcula tablas P y M para un sensor específico.
    Returns: (P_table, M_table)
    """
    # Inicializar P[d] = 0
    P_table = {d: 0x000 for d in range(10)}
    
    for iteration in range(iterations):
        # Calcular M[e] usando P[d] actual
        M_candidates = defaultdict(Counter)
        
        for temp_c, r12, _ in frames:
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
        
        # Recalcular P[d] usando M[e]
        P_candidates = defaultdict(Counter)
        
        for temp_c, r12, _ in frames:
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
    
    # Recalcular M final con P final
    M_candidates = defaultdict(Counter)
    for temp_c, r12, _ in frames:
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


def verify_tables(frames: List[Tuple[float, int, str]], M_table: Dict[int, int], P_table: Dict[int, int]) -> Tuple[int, int]:
    """Verifica precisión de las tablas."""
    correct = 0
    errors = 0
    
    for temp_c, r12_observed, _ in frames:
        try:
            e, d = temp_to_e_d(temp_c)
        except ValueError:
            continue
        
        if e not in M_table or d not in P_table:
            continue
        
        r12_calculated = M_table[e] ^ P_table[d]
        
        if r12_calculated == r12_observed:
            correct += 1
        else:
            errors += 1
    
    return correct, errors


def generate_documentation(results: Dict[str, Tuple], csv_path: str):
    """Genera documentación con las tablas por sensor."""
    doc_path = "tablas_M_P_por_sensor.md"
    
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write("# Tablas M y P por Sensor\n\n")
        f.write(f"**Archivo analizado:** {csv_path}\n\n")
        f.write("---\n\n")
        
        for house in sorted(results.keys(), key=lambda x: results[x][3], reverse=True):
            P_table, M_table, correct, errors, total = results[house]
            precision = 100 * correct / (correct + errors) if (correct + errors) > 0 else 0
            
            f.write(f"## Sensor House Code: {house}\n\n")
            f.write(f"**Tramas analizadas:** {total}\n")
            f.write(f"**Tramas correctas:** {correct}\n")
            f.write(f"**Tramas con error:** {errors}\n")
            f.write(f"**Precisión:** {precision:.2f}%\n\n")
            
            f.write("### Tabla P[d]\n\n")
            f.write("| d | P[d] (hex) | P[d] (dec) |\n")
            f.write("|---|------------|------------|\n")
            for d in range(10):
                if d in P_table:
                    f.write(f"| {d} | 0x{P_table[d]:03X} | {P_table[d]:4d} |\n")
            
            f.write("\n### Tabla M[e] (primeras 20 entradas)\n\n")
            f.write("| e (°C) | M[e] (hex) | M[e] (dec) |\n")
            f.write("|--------|------------|------------|\n")
            for i, e in enumerate(sorted(M_table.keys())[:20]):
                f.write(f"| {e:4d} | 0x{M_table[e]:03X} | {M_table[e]:4d} |\n")
            
            if len(M_table) > 20:
                f.write(f"\n*... y {len(M_table) - 20} entradas más*\n")
            
            f.write("\n### Código Python\n\n")
            f.write("```python\n")
            f.write(f"# Sensor House {house}\n")
            f.write("P_TABLE = [\n")
            for d in range(10):
                if d in P_table:
                    f.write(f"    0x{P_table[d]:03X},  # P[{d}]\n")
            f.write("]\n\n")
            f.write("M_TABLE = {\n")
            for e in sorted(M_table.keys()):
                f.write(f"    {e:4d}: 0x{M_table[e]:03X},\n")
            f.write("}\n")
            f.write("```\n\n")
            f.write("---\n\n")
    
    print(f"\nDocumentación generada en: {doc_path}")


def main(csv_path: str):
    print(f"Analizando: {csv_path}")
    print(f"Preámbulo requerido: {KNOWN_PREAMBLE}\n")
    
    # Cargar tramas por sensor
    frames_by_sensor = load_frames_by_sensor(csv_path)
    
    if not frames_by_sensor:
        print("ERROR: No se encontraron tramas válidas")
        return
    
    # Procesar cada sensor
    results = {}
    
    for house in sorted(frames_by_sensor.keys(), key=lambda x: len(frames_by_sensor[x]), reverse=True):
        frames = frames_by_sensor[house]
        print(f"\n{'='*60}")
        print(f"Procesando sensor House {house} ({len(frames)} tramas)")
        print('='*60)
        
        # Calcular tablas
        P_table, M_table = calculate_tables_for_sensor(frames)
        
        print(f"\nTabla P[d]:")
        for d in range(10):
            if d in P_table:
                print(f"  P[{d}] = 0x{P_table[d]:03X}")
        
        print(f"\nTabla M[e]: {len(M_table)} temperaturas")
        
        # Verificar
        correct, errors = verify_tables(frames, M_table, P_table)
        precision = 100 * correct / (correct + errors) if (correct + errors) > 0 else 0
        print(f"\nVerificación:")
        print(f"  Correctas: {correct}")
        print(f"  Errores: {errors}")
        print(f"  Precisión: {precision:.2f}%")
        
        results[house] = (P_table, M_table, correct, errors, len(frames))
    
    # Generar documentación
    generate_documentation(results, csv_path)
    
    print("\n¡Proceso completado!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 recalc_M_P_per_sensor.py ec40_capturas_merged.csv")
        sys.exit(1)
    
    main(sys.argv[1])
