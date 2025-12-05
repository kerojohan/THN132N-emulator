#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Análisis del patrón 80/20 en Houses 3 vs 96
¿Qué determina cuándo usar 0x3DB vs 0x9A3?
- ¿Temperatura?
- ¿Décima?
- ¿Parte entera?
- ¿Nibble de algún valor?
"""

import csv
from collections import defaultdict

def temp_to_e_d(temp_c):
    """Descompone temperatura en parte entera e y décima d."""
    e = int(temp_c)
    t10 = int(round(abs(temp_c * 10)))
    d = t10 - abs(e) * 10
    return e, d


def analyze_3_vs_96_pattern():
    """Analiza el patrón condicional entre Houses 3 y 96."""
    
    print("="*80)
    print("ANÁLISIS DE PATRÓN CONDICIONAL: Houses 3 vs 96")
    print("="*80)
    
    # Cargar datos limpios
    data = []
    with open("../ec40_capturas_merged_clean.csv", newline='') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        
        for row in reader:
            if len(row) >= 4:
                house = int(row[0])
                temp = float(row[1])
                r12 = int(row[2], 16)
                
                if house in [3, 96]:
                    e, d = temp_to_e_d(temp)
                    data.append({
                        'house': house,
                        'temp': temp,
                        'e': e,
                        'd': d,
                        'r12': r12
                    })
    
    # Agrupar por temperatura
    by_temp = defaultdict(lambda: {'3': None, '96': None})
    
    for frame in data:
        house_key = str(frame['house'])
        by_temp[frame['temp']][house_key] = frame
    
    # Analizar solo temperaturas con ambos houses
    comparisons = []
    
    for temp, houses_data in by_temp.items():
        if houses_data['3'] is not None and houses_data['96'] is not None:
            r12_3 = houses_data['3']['r12']
            r12_96 = houses_data['96']['r12']
            xor_val = r12_3 ^ r12_96
            
            comparisons.append({
                'temp': temp,
                'e': houses_data['3']['e'],
                'd': houses_data['3']['d'],
                'r12_3': r12_3,
                'r12_96': r12_96,
                'xor': xor_val
            })
    
    print(f"\nTemperaturas con ambos houses: {len(comparisons)}")
    
    # Separar por XOR value
    xor_3db = [c for c in comparisons if c['xor'] == 0x3DB]
    xor_9a3 = [c for c in comparisons if c['xor'] == 0x9A3]
    other_xor = [c for c in comparisons if c['xor'] not in [0x3DB, 0x9A3]]
    
    print(f"\nDistribución de XOR:")
    print(f"  0x3DB: {len(xor_3db)} casos ({100*len(xor_3db)/len(comparisons):.1f}%)")
    print(f"  0x9A3: {len(xor_9a3)} casos ({100*len(xor_9a3)/len(comparisons):.1f}%)")
    print(f"  Otros: {len(other_xor)} casos ({100*len(other_xor)/len(comparisons):.1f}%)")
    
    # Analizar características de cada grupo
    print("\n" + "="*80)
    print("CARACTERÍSTICAS DEL GRUPO XOR = 0x3DB")
    print("="*80)
    
    print(f"\nTemperaturas enteras:")
    e_values_3db = sorted(set(c['e'] for c in xor_3db))
    print(f"  {e_values_3db}")
    
    print(f"\nDécimas:")
    d_values_3db = sorted(set(c['d'] for c in xor_3db))
    print(f"  {d_values_3db}")
    
    print(f"\nRango temperatura:")
    temps_3db = [c['temp'] for c in xor_3db]
    print(f"  {min(temps_3db):.1f}°C - {max(temps_3db):.1f}°C")
    
    print("\n" + "="*80)
    print("CARACTERÍSTICAS DEL GRUPO XOR = 0x9A3")
    print("="*80)
    
    print(f"\nTemperaturas enteras:")
    e_values_9a3 = sorted(set(c['e'] for c in xor_9a3))
    print(f"  {e_values_9a3}")
    
    print(f"\nDécimas:")
    d_values_9a3 = sorted(set(c['d'] for c in xor_9a3))
    print(f"  {d_values_9a3}")
    
    print(f"\nRango temperatura:")
    temps_9a3 = [c['temp'] for c in xor_9a3]
    print(f"  {min(temps_9a3):.1f}°C - {max(temps_9a3):.1f}°C")
    
    # Buscar patrón
    print("\n" + "="*80)
    print("BÚSQUEDA DE PATRÓN DISCRIMINANTE")
    print("="*80)
    
    # ¿Es por temperatura entera?
    e_only_3db = set(e_values_3db) - set(e_values_9a3)
    e_only_9a3 = set(e_values_9a3) - set(e_values_3db)
    e_both = set(e_values_3db) & set(e_values_9a3)
    
    if len(e_both) == 0:
        print(f"\n✓✓✓ PATRÓN ENCONTRADO: Depende de temperatura entera!")
        print(f"  XOR 0x3DB para e en {e_values_3db}")
        print(f"  XOR 0x9A3 para e en {e_values_9a3}")
    else:
        print(f"\n✗ NO es solo por temperatura entera (ambos comparten: {sorted(e_both)})")
    
    # ¿Es por décima?
    d_only_3db = set(d_values_3db) - set(d_values_9a3)
    d_only_9a3 = set(d_values_9a3) - set(d_values_3db)
    d_both = set(d_values_3db) & set(d_values_9a3)
    
    if len(d_both) == 0:
        print(f"\n✓✓✓ PATRÓN ENCONTRADO: Depende de décima!")
        print(f"  XOR 0x3DB para d en {d_values_3db}")
        print(f"  XOR 0x9A3 para d in {d_values_9a3}")
    else:
        print(f"\n✗ NO es solo por décima (ambos comparten: {sorted(d_both)})")
    
    # Mostrar tabla detallada
    print("\n" + "="*80)
    print("TABLA DETALLADA POR TEMPERATURA Y DÉCIMA")
    print("="*80)
    
    # Crear matriz e x d
    matrix = defaultdict(lambda: defaultdict(lambda: None))
    
    for c in comparisons:
        matrix[c['e']][c['d']] = c['xor']
    
    # Mostrar matriz
    print("\n     ", end="")
    for d in range(10):
        print(f"  d={d}", end="")
    print()
    
    for e in sorted(matrix.keys()):
        print(f"e={e:2d} ", end="")
        for d in range(10):
            xor = matrix[e][d]
            if xor == 0x3DB:
                print("  3DB", end="")
            elif xor == 0x9A3:
                print("  9A3", end="")
            elif xor is not None:
                print(f"{xor:5X}", end="")
            else:
                print("    -", end="")
        print()


if __name__ == "__main__":
    analyze_3_vs_96_pattern()
