#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Búsqueda avanzada de reglas de transformación
Ya que XOR simple no funciona, buscar:
1. Transformaciones por nibbles
2. Rotaciones de bits
3. Offsets + XOR
4. Patrones específicos por rango de temperatura
"""

import csv
from collections import defaultdict
from typing import Dict, Tuple, List

def temp_to_e_d(temp_c: float) -> Tuple[int, int]:
    """Descompone temperatura en parte entera e y décima d."""
    e = int(temp_c)
    t10 = int(round(abs(temp_c * 10)))
    d = t10 - abs(e) * 10
    if d < 0 or d > 9:
        raise ValueError(f"décima fuera de rango para temp={temp_c}: d={d}")
    return e, d


def load_clean_data(csv_path: str):
    """Carga datos limpios."""
    data = []
    with open(csv_path, newline='') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        
        for row in reader:
            if len(row) >= 4:
                house = int(row[0])
                temp = float(row[1])
                r12 = int(row[2], 16)
                data.append({'house': house, 'temp': temp, 'r12': r12})
    
    return data


def search_advanced_patterns():
    """Búsqueda avanzada de patrones de transformación."""
    
    print("="*80)
    print("BÚSQUEDA AVANZADA DE REGLAS DE TRANSFORMACIÓN")
    print("="*80)
    
    clean_path = "../ec40_capturas_merged_clean.csv"
    data = load_clean_data(clean_path)
    
    print(f"\nDatos cargados: {len(data)} frames limpios")
    
    # Agrupar por house y temperatura para comparar
    by_house_temp = defaultdict(list)
    for frame in data:
        key = (frame['house'], frame['temp'])
        by_house_temp[key].append(frame['r12'])
    
    # Para cada par de houses, buscar temperaturas idénticas
    houses = sorted(set(f['house'] for f in data))
    print(f"Houses: {houses}")
    
    print("\n" + "="*80)
    print("ANÁLISIS: MISMA TEMPERATURA EN DIFERENTES HOUSES")
    print("="*80)
    
    # Buscar temperaturas que aparecen en múltiples houses
    temps_by_houses = defaultdict(set)
    for (house, temp), r12_values in by_house_temp.items():
        temps_by_houses[temp].add(house)
    
    # Solo temperaturas con al menos 2 houses
    common_temps = {t: houses for t, houses in temps_by_houses.items() if len(houses) >= 2}
    
    print(f"\nTemperaturas con datos de múltiples houses: {len(common_temps)}")
    
    # Analizar transformaciones para temperaturas comunes
    print("\n" + "-"*80)
    print("BUSCANDO PATRONES ENTRE HOUSES:")
    print("-"*80)
    
    transformation_candidates = []
    
    for temp in sorted(common_temps.keys()):
        houses_with_temp = sorted(common_temps[temp])
        
        if len(houses_with_temp) < 2:
            continue
        
        # Obtener R12 para cada house en esta temperatura
        r12_values = {}
        for h in houses_with_temp:
            key = (h, temp)
            if key in by_house_temp:
                # Tomar el valor más frecuente
                r12_list = by_house_temp[key]
                r12_values[h] = max(set(r12_list), key=r12_list.count)
        
        # Comparar pares
        for i, h1 in enumerate(houses_with_temp):
            for h2 in houses_with_temp[i+1:]:
                if h1 in r12_values and h2 in r12_values:
                    r1 = r12_values[h1]
                    r2 = r12_values[h2]
                    
                    # Calcular diferentes transformaciones posibles
                    xor_val = r1 ^ r2
                    diff = abs(r1 - r2)
                    house_xor = h1 ^ h2
                    
                    transformation_candidates.append({
                        'temp': temp,
                        'h1': h1,
                        'h2': h2,
                        'r1': r1,
                        'r2': r2,
                        'xor': xor_val,
                        'diff': diff,
                        'house_xor': house_xor
                    })
    
    print(f"\nTotal comparaciones: {len(transformation_candidates)}")
    
    # Agrupar por par de houses
    by_house_pair = defaultdict(list)
    for t in transformation_candidates:
        pair = (t['h1'], t['h2'])
        by_house_pair[pair].append(t)
    
    print(f"\nPares de houses analizados: {len(by_house_pair)}")
    
    # Analizar cada par
    for (h1, h2), transforms in sorted(by_house_pair.items()):
        if len(transforms) < 3:
            continue
        
        print(f"\n{'-'*80}")
        print(f"Houses {h1} (0x{h1:02X}) vs {h2} (0x{h2:02X}): {len(transforms)} temperaturas comunes")
        
        # XORs
        xors = [t['xor'] for t in transforms]
        unique_xors = set(xors)
        
        if len(unique_xors) == 1:
            xor = list(unique_xors)[0]
            print(f"  ✓✓✓ R12 XOR CONSTANTE = 0x{xor:03X}")
            print(f"      House XOR = 0x{h1^h2:02X}")
        elif len(unique_xors) <= 3:
            print(f"  ~ R12 XOR casi constante ({len(unique_xors)} valores):")
            for xor_val in sorted(unique_xors):
                count = xors.count(xor_val)
                pct = 100 * count / len(xors)
                print(f"      0x{xor_val:03X}: {count}/{len(xors)} ({pct:.1f}%)")
        
        # Diferencias absolutas
        diffs = [t['diff'] for t in transforms]
        unique_diffs = set(diffs)
        
        if len(unique_diffs) <= 3:
            print(f"  Diferencias absolutas ({len(unique_diffs)} valores):")
            for diff in sorted(unique_diffs):
                count = diffs.count(diff)
                pct = 100 * count / len(diffs)
                print(f"      {diff}: {count}/{len(diffs)} ({pct:.1f}%)")
        
        # Mostrar ejemplos
        print(f"  Ejemplos:")
        for t in transforms[:3]:
            print(f"    {t['temp']:5.1f}°C: R12[{h1}]=0x{t['r1']:03X}, R12[{h2}]=0x{t['r2']:03X}, " +
                  f"XOR=0x{t['xor']:03X}, diff={t['diff']}")


if __name__ == "__main__":
    search_advanced_patterns()
