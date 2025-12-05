#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Detección y filtrado de outliers en datos capturados
Estrategia:
1. Para cada (house, temperatura), encontrar valor R12 más frecuente
2. Marcar como outliers los valores que difieren significativamente
3. Re-calcular tablas M y P con datos limpios
4. Buscar regla universal de transformación
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


def detect_outliers(csv_path: str):
    """Detecta outliers en los datos capturados."""
    
    print("="*80)
    print("DETECCIÓN DE OUTLIERS EN DATOS CAPTURADOS")
    print("="*80)
    
    # Agrupar por (house, temp) → [r12 values]
    r12_by_house_temp = defaultdict(list)
    all_frames = []
    
    with open(csv_path, newline='') as f:
        reader = csv.reader(f)
        first = True
        
        for row_num, row in enumerate(reader, 1):
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
                
                key = (house, temp_c)
                r12_by_house_temp[key].append(r12)
                all_frames.append({
                    'row': row_num,
                    'house': house,
                    'temp': temp_c,
                    'r12': r12,
                    'ec40': ec40_hex
                })
            except Exception:
                continue
    
    print(f"\nTotal frames cargados: {len(all_frames)}")
    
    # Detectar outliers: valores R12 que aparecen solo 1 vez cuando hay múltiples capturas
    print("\n" + "="*80)
    print("1. DETECCIÓN DE VALORES INCONSISTENTES")
    print("="*80)
    
    outliers = []
    clean_frames = []
    
    for frame in all_frames:
        key = (frame['house'], frame['temp'])
        r12_values = r12_by_house_temp[key]
        
        # Si hay múltiples capturas de la misma temperatura
        if len(r12_values) > 1:
            # Contar frecuencias
            counter = Counter(r12_values)
            most_common_r12, most_common_count = counter.most_common(1)[0]
            
            # Si el valor actual NO es el más común y solo aparece 1 vez
            if frame['r12'] != most_common_r12 and counter[frame['r12']] == 1:
                outliers.append({
                    **frame,
                    'reason': f"R12 único (esperado: 0x{most_common_r12:03X}, encontrado {most_common_count}x)",
                    'expected': most_common_r12
                })
            else:
                clean_frames.append(frame)
        else:
            # Solo hay una captura, aceptarla (no podemos validar)
            clean_frames.append(frame)
    
    print(f"\nFrames limpios: {len(clean_frames)}")
    print(f"Outliers detectados: {len(outliers)}")
    
    if outliers:
        print(f"\nEjemplos de outliers detectados:")
        for i, outlier in enumerate(outliers[:10]):
            print(f"  {i+1}. House {outlier['house']:3d}, Temp {outlier['temp']:5.1f}°C")
            print(f"      R12 = 0x{outlier['r12']:03X}, {outlier['reason']}")
    
    # Analizar distribución de outliers por house
    print("\n" + "="*80)
    print("2. DISTRIBUCIÓN DE OUTLIERS POR HOUSE")
    print("="*80)
    
    outliers_by_house = defaultdict(int)
    total_by_house = defaultdict(int)
    
    for frame in all_frames:
        total_by_house[frame['house']] += 1
    
    for outlier in outliers:
        outliers_by_house[outlier['house']] += 1
    
    for house in sorted(total_by_house.keys()):
        total = total_by_house[house]
        out_count = outliers_by_house[house]
        pct = 100 * out_count / total if total > 0 else 0
        status = "⚠️" if pct > 10 else "✓"
        print(f"{status} House {house:3d}: {out_count:3d}/{total:3d} outliers ({pct:5.1f}%)")
    
    # Guardar frames limpios a CSV
    print("\n" + "="*80)
    print("3. GUARDANDO DATOS LIMPIOS")
    print("="*80)
    
    clean_csv_path = csv_path.replace('.csv', '_clean.csv')
    
    with open(clean_csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['house', 'temp_c', 'r12_hex', 'ec40_hex'])
        
        for frame in clean_frames:
            writer.writerow([
                frame['house'],
                frame['temp'],
                f"0x{frame['r12']:03X}",
                frame['ec40']
            ])
    
    print(f"\n✓ Datos limpios guardados en: {clean_csv_path}")
    print(f"  Total frames: {len(clean_frames)}")
    print(f"  Outliers removidos: {len(outliers)} ({100*len(outliers)/len(all_frames):.1f}%)")
    
    return clean_frames, outliers, clean_csv_path


def calculate_tables_clean(frames: List[Dict]) -> Tuple[Dict, Dict]:
    """Calcula tablas M y P con datos limpios."""
    P_table = {d: 0x000 for d in range(10)}
    
    frame_tuples = [(f['temp'], f['r12']) for f in frames]
    
    for iteration in range(10):
        M_candidates = defaultdict(Counter)
        
        for temp_c, r12 in frame_tuples:
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
        
        for temp_c, r12 in frame_tuples:
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


def analyze_clean_data(clean_frames: List[Dict]):
    """Analiza datos limpios para buscar regla universal."""
    
    print("\n" + "="*80)
    print("4. ANÁLISIS CON DATOS LIMPIOS")
    print("="*80)
    
    # Agrupar por house
    by_house = defaultdict(list)
    for frame in clean_frames:
        by_house[frame['house']].append(frame)
    
    # Calcular tablas para cada house
    m_tables = {}
    p_tables = {}
    
    for house in sorted(by_house.keys()):
        if len(by_house[house]) >= 10:
            m_table, p_table = calculate_tables_clean(by_house[house])
            m_tables[house] = m_table
            p_tables[house] = p_table
            print(f"\nHouse {house:3d}: {len(by_house[house])} frames limpios")
            print(f"  Tabla P: {[f'0x{p_table[d]:03X}' for d in range(10)]}")
    
    # Buscar XOR en tabla M con datos limpios
    print("\n" + "="*80)
    print("5. BÚSQUEDA DE XOR EN TABLA M (DATOS LIMPIOS)")
    print("="*80)
    
    houses = sorted(m_tables.keys())
    
    for i in range(len(houses)):
        for j in range(i+1, len(houses)):
            h1, h2 = houses[i], houses[j]
            
            common_temps = set(m_tables[h1].keys()) & set(m_tables[h2].keys())
            
            if len(common_temps) < 5:
                continue
            
            # Calcular XORs
            xor_values = []
            for temp in sorted(common_temps):
                m1 = m_tables[h1][temp]
                m2 = m_tables[h2][temp]
                xor_val = m1 ^ m2
                xor_values.append(xor_val)
            
            unique_xors = set(xor_values)
            
            print(f"\nHouses {h1} vs {h2} ({len(common_temps)} temps comunes):")
            
            if len(unique_xors) == 1:
                xor_mask = list(unique_xors)[0]
                print(f"  ✓✓✓ XOR CONSTANTE = 0x{xor_mask:03X} ← ¡REGLA ENCONTRADA!")
                
                # Verificar relación con house codes
                house_xor = h1 ^ h2
                print(f"  House codes: {h1} (0x{h1:02X}) vs {h2} (0x{h2:02X})")
                print(f"  House XOR: 0x{house_xor:02X}")
                
                if xor_mask == house_xor:
                    print(f"  ✓✓✓ M_XOR == HOUSE_XOR → Regla universal!")
                
            elif len(unique_xors) <= 3:
                print(f"  ~ XOR casi constante: {len(unique_xors)} valores")
                for xor_val in sorted(unique_xors):
                    count = xor_values.count(xor_val)
                    pct = 100 * count / len(xor_values)
                    print(f"    0x{xor_val:03X}: {count}/{len(xor_values)} ({pct:.1f}%)")
            else:
                print(f"  ✗ Sin patrón ({len(unique_xors)} valores diferentes)")


def main(csv_path: str):
    """Función principal."""
    clean_frames, outliers, clean_csv_path = detect_outliers(csv_path)
    analyze_clean_data(clean_frames)
    
    print("\n" + "="*80)
    print("RESUMEN")
    print("="*80)
    print(f"\nArchivo original: {csv_path}")
    print(f"Archivo limpio: {clean_csv_path}")
    print(f"\nFrames totales: {len(clean_frames) + len(outliers)}")
    print(f"Frames limpios: {len(clean_frames)}")
    print(f"Outliers removidos: {len(outliers)}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        csv_path = "ec40_capturas_merged.csv"
        print(f"Usando archivo por defecto: {csv_path}\n")
    else:
        csv_path = sys.argv[1]
    
    main(csv_path)
