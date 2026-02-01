#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Descubrimiento: Las tablas P se derivan del house code mediante XOR.

Patrón encontrado:
- House 3 tiene una tabla P base
- House 247: P[d] = P_base[d] XOR 0x075 (con permutación)
- El house code actúa como semilla para derivar la tabla P

Este script intenta encontrar la función de derivación exacta.
"""

import csv
from collections import Counter, defaultdict

KNOWN_PREAMBLE = "555555559995a5a6aa6a"

# Tablas P conocidas (de nuestro análisis previo)
KNOWN_P_TABLES = {
    3: [0x075, 0x000, 0x09F, 0x0EA, 0x0C0, 0x0B5, 0x02A, 0x05F, 0x01E, 0x06B],
    247: [0x000, 0x075, 0x0EA, 0x09F, 0x0B5, 0x0C0, 0x05F, 0x02A, 0x06B, 0x01E],
    96: [0x01E, 0x01E, 0x0F4, 0x081, 0x0DE, 0x0DE, 0x034, 0x034, 0x000, 0x000],
}


def analyze_xor_pattern():
    """Analiza el patrón XOR entre las tablas P."""
    
    print("Análisis detallado del patrón XOR")
    print("="*70)
    print()
    
    base_house = 3
    base_table = KNOWN_P_TABLES[base_house]
    
    for house, table in KNOWN_P_TABLES.items():
        if house == base_house:
            continue
        
        print(f"House {house} vs House {base_house}:")
        print(f"  House {house} = 0x{house:02X}, House {base_house} = 0x{base_house:02X}")
        print(f"  XOR de houses: 0x{house ^ base_house:02X}")
        print()
        
        # Analizar cada posición
        print("  d | P_base | P_house | XOR  | Relación")
        print("  " + "-"*50)
        
        for d in range(10):
            xor_val = base_table[d] ^ table[d]
            
            # Buscar si P_house[d] aparece en P_base
            if table[d] in base_table:
                pos = base_table.index(table[d])
                relation = f"P_base[{pos}]"
            else:
                relation = "nuevo valor"
            
            print(f"  {d} | 0x{base_table[d]:03X}  | 0x{table[d]:03X}  | 0x{xor_val:03X} | {relation}")
        
        print()
        
        # Ver si hay un patrón en el XOR
        xor_values = [base_table[d] ^ table[d] for d in range(10)]
        unique_xors = set(xor_values)
        
        print(f"  Valores XOR únicos: {len(unique_xors)}")
        if len(unique_xors) <= 3:
            for xor_val in sorted(unique_xors):
                positions = [d for d in range(10) if xor_values[d] == xor_val]
                print(f"    0x{xor_val:03X}: posiciones {positions}")
        
        print()


def test_derivation_hypothesis():
    """Prueba hipótesis de derivación basada en house code."""
    
    print("\nProbando hipótesis de derivación")
    print("="*70)
    print()
    
    # Hipótesis 1: Rotación basada en house code
    print("Hipótesis 1: Rotación de la tabla base")
    base_table = KNOWN_P_TABLES[3]
    
    for house, expected_table in KNOWN_P_TABLES.items():
        if house == 3:
            continue
        
        # Probar diferentes rotaciones
        for shift in range(10):
            rotated = base_table[shift:] + base_table[:shift]
            if rotated == expected_table:
                print(f"  House {house}: rotación de {shift} posiciones ✓")
                print(f"    Relación con house: shift = {shift}, house % 10 = {house % 10}")
                break
        else:
            print(f"  House {house}: NO es una rotación simple ✗")
    
    print()
    
    # Hipótesis 2: Permutación basada en house code
    print("Hipótesis 2: Permutación de índices")
    
    for house, table in KNOWN_P_TABLES.items():
        if house == 3:
            continue
        
        # Encontrar la permutación
        permutation = []
        for d in range(10):
            if table[d] in base_table:
                permutation.append(base_table.index(table[d]))
            else:
                permutation.append(-1)
        
        print(f"  House {house}: permutación = {permutation}")
        
        # Ver si hay un patrón
        if -1 not in permutation:
            # Calcular diferencias
            diffs = [(permutation[i] - i) % 10 for i in range(10)]
            if len(set(diffs)) == 1:
                print(f"    → Shift constante de {diffs[0]} posiciones")
            else:
                print(f"    → Patrón complejo: {diffs}")
        
        print()


def derive_p_table_from_house(house_code, base_table=None):
    """
    Intenta derivar la tabla P a partir del house code.
    
    Basado en los patrones observados:
    - House 3 parece ser la base
    - House 247 = permutación de House 3
    """
    
    if base_table is None:
        base_table = KNOWN_P_TABLES[3]
    
    # Por ahora, retornar la tabla conocida si existe
    if house_code in KNOWN_P_TABLES:
        return KNOWN_P_TABLES[house_code]
    
    # Para otros house codes, usar la tabla base
    # (esto es una aproximación hasta que encontremos el patrón exacto)
    return base_table


def main():
    analyze_xor_pattern()
    test_derivation_hypothesis()
    
    print("\n" + "="*70)
    print("CONCLUSIÓN")
    print("="*70)
    print()
    print("Las tablas P están relacionadas pero no mediante una simple rotación.")
    print("El patrón exacto de derivación requiere más análisis.")
    print()
    print("Para uso práctico:")
    print("  - Usa la tabla P específica del house code que quieras emular")
    print("  - Las tablas están en: tablas_M_P_por_sensor.md")
    print()
    print("Tablas P conocidas:")
    for house in sorted(KNOWN_P_TABLES.keys()):
        print(f"  House {house:3d}: {[f'0x{x:03X}' for x in KNOWN_P_TABLES[house]]}")


if __name__ == "__main__":
    main()
