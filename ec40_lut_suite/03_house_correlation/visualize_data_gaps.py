#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Visualización del estado de datos capturados vs necesarios
Muestra gaps y prioridades de captura
"""

import csv
from collections import defaultdict

def visualize_data_coverage():
    """Muestra cobertura actual de datos."""
    
    print("="*80)
    print("ANÁLISIS DE COBERTURA DE DATOS")
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
                e = int(temp)
                data.append({'house': house, 'temp': temp, 'e': e})
    
    # Agrupar por house
    by_house = defaultdict(list)
    for frame in data:
        by_house[frame['house']].append(frame)
    
    print(f"\n📊 DATOS ACTUALES")
    print("-"*80)
    
    for house in sorted(by_house.keys()):
        frames = by_house[house]
        temps_e = sorted(set(f['e'] for f in frames))
        temp_range = (min(temps_e), max(temps_e))
        
        print(f"\nHouse {house:3d} (0x{house:02X}):")
        print(f"  Frames: {len(frames)}")
        print(f"  Rango: {temp_range[0]}°C a {temp_range[1]}°C")
        print(f"  Temperaturas enteras: {len(temps_e)}")
    
    # Análisis de pares de houses
    print(f"\n📈 TEMPERATURAS COMUNES ENTRE HOUSES")
    print("-"*80)
    
    houses = sorted(by_house.keys())
    
    # Houses prioritarios
    priority_pairs = [
        (3, 96, "🔴 ALTA", "Extender XOR condicional"),
        (3, 247, " 🔴 ALTA", "Buscar patrón condicional"),
        (96, 247, "🟡 MEDIA", "Caracterizar transformación"),
    ]
    
    for h1, h2, priority, desc in priority_pairs:
        if h1 in by_house and h2 in by_house:
            temps1 = set(f['e'] for f in by_house[h1])
            temps2 = set(f['e'] for f in by_house[h2])
            common = sorted(temps1 & temps2)
            
            print(f"\n{priority} Houses {h1} ↔ {h2}: {desc}")
            print(f"  Temperaturas comunes: {len(common)}")
            if common:
                print(f"  Rango: {min(common)}°C a {max(common)}°C")
                print(f"  Valores: {common}")
    
    # Gaps identificados
    print(f"\n❌ GAPS CRÍTICOS")
    print("-"*80)
    
    gaps = [
        {
            'priority': '🔴',
            'houses': [3, 96],
            'desc': 'Extender rango <26°C y >33°C',
            'current': '26-33°C',
            'needed': '-10 a 60°C',
            'frames': 300
        },
        {
            'priority': '🔴',
            'houses': [3, 247],
            'desc': 'Temperaturas idénticas en rangos',
            'current': 'Dispersas',
            'needed': '5 rangos × 10 temps',
            'frames': 150
        },
        {
            'priority': '🔴',
            'houses': [0, 92, 135],
            'desc': 'Validación completa',
            'current': '2-6 frames',
            'needed': '150 frames cada uno',
            'frames': 450
        },
    ]
    
    for gap in gaps:
        print(f"\n{gap['priority']} Houses {gap['houses']}: {gap['desc']}")
        print(f"  Estado actual: {gap['current']}")
        print(f"  Necesario: {gap['needed']}")
        print(f"  Frames estimados: {gap['frames']}")
    
    # Resumen
    print(f"\n" + "="*80)
    print("RESUMEN")
    print("="*80)
    
    total_current = len(data)
    total_needed = 2490
    total_high_priority = 900
    
    print(f"\n📊 Frames actuales (limpios): {total_current}")
    print(f"📊 Frames necesarios: ~{total_needed}")
    print(f"🔴 Alta prioridad: {total_high_priority}")
    
    print(f"\nCobertura estimada: {100*total_current/(total_current+total_needed):.1f}%")
    
    print(f"\n💡 PRÓXIMO PASO")
    print("-"*80)
    print("1. Configurar 2 sensores: House 3 y House 96")
    print("2. Capturar temperaturas: -10 a 25°C (incrementos 0.5°C)")
    print("3. Capturar temperaturas: 34 a 60°C (incrementos 0.5°C)")
    print("4. Mínimo 3 capturas por temperatura")
    print("\nObjetivo: Validar XOR condicional en todo el rango")


if __name__ == "__main__":
    visualize_data_coverage()
