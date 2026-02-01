#!/usr/bin/env python3
"""
Investigació exhaustiva de TOTS els House IDs per determinar si el generador
pot ser completament universal.
"""

import csv
from collections import defaultdict
import sys

# Carregar totes les captures i agrupar per House ID
captures_by_house = defaultdict(list)

print("="*80)
print("INVESTIGACIÓ EXHAUSTIVA DE TOTS ELS HOUSE IDs")
print("="*80)

print("\nCarregant captures...")
with open('../ec40_all_captures_normalized.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        house = int(row['house'])
        temp_c = float(row['temperature_C'])
        payload = row['payload64_hex']
        
        if len(payload) >= 15:
            nibbles = [int(c, 16) for c in payload]
            p = nibbles[14]
            nib7 = nibbles[7]
            temp_idx = int(round((temp_c + 40) * 10))
            
            captures_by_house[house].append({
                'temp_idx': temp_idx,
                'temp_c': temp_c,
                'nib7': nib7,
                'p': p
            })

print(f"Total House IDs trobats: {len(captures_by_house)}")
print(f"Houses: {sorted(captures_by_house.keys())}")

# Estadístiques per House
print("\n" + "="*80)
print("ESTADÍSTIQUES PER HOUSE ID")
print("="*80)
print(f"\n{'House':>6} | {'Captures':>8} | {'Temps úniques':>14} | {'Nib7 valors':>12} | {'Rang Temp':>20}")
print("-"*80)

for house in sorted(captures_by_house.keys()):
    caps = captures_by_house[house]
    temps_uniques = len(set(c['temp_idx'] for c in caps))
    nib7_vals = sorted(set(c['nib7'] for c in caps))
    min_temp = min(c['temp_c'] for c in caps)
    max_temp = max(c['temp_c'] for c in caps)
    
    nib7_str = ','.join([f'0x{n:X}' for n in nib7_vals])
    print(f"{house:6} | {len(caps):8} | {temps_uniques:14} | {nib7_str:12} | {min_temp:5.1f}°C - {max_temp:5.1f}°C")

# Buscar transformacions XOR amb House 247 (base de referència)
print("\n" + "="*80)
print("TRANSFORMACIONS XOR AMB HOUSE 247 (BASE)")
print("="*80)

if 247 not in captures_by_house:
    print("❌ House 247 no trobat al dataset!")
    sys.exit(1)

base_house = 247
base_data = {}

# Indexar House 247 per (temp_idx, nib7)
for cap in captures_by_house[base_house]:
    key = (cap['temp_idx'], cap['nib7'])
    if key not in base_data:
        base_data[key] = []
    base_data[key].append(cap['p'])

print(f"\nHouse {base_house} (base): {len(base_data)} claus (temp, nib7) úniques")

# Comparar cada House amb la base
results = []

for house in sorted(captures_by_house.keys()):
    if house == base_house:
        continue
    
    # Trobar claus comunes
    house_data = {}
    for cap in captures_by_house[house]:
        key = (cap['temp_idx'], cap['nib7'])
        if key not in house_data:
            house_data[key] = []
        house_data[key].append(cap['p'])
    
    common_keys = set(base_data.keys()) & set(house_data.keys())
    
    if len(common_keys) < 3:  # Mínim 3 punts per comparar
        results.append({
            'house': house,
            'common': len(common_keys),
            'xor': None,
            'constant': False,
            'note': 'Poques dades comunes'
        })
        continue
    
    # Calcular XORs
    xor_values = []
    for key in common_keys:
        p_base = base_data[key][0]
        p_house = house_data[key][0]
        xor_val = p_base ^ p_house
        xor_values.append(xor_val)
    
    # Comprovar si XOR és constant
    unique_xors = set(xor_values)
    is_constant = len(unique_xors) == 1
    
    if is_constant:
        xor_constant = list(unique_xors)[0]
        results.append({
            'house': house,
            'common': len(common_keys),
            'xor': xor_constant,
            'constant': True,
            'note': '✅ XOR constant'
        })
    else:
        # Calcular XOR més freqüent
        from collections import Counter
        xor_counts = Counter(xor_values)
        most_common_xor, count = xor_counts.most_common(1)[0]
        percentage = count / len(xor_values) * 100
        
        results.append({
            'house': house,
            'common': len(common_keys),
            'xor': most_common_xor,
            'constant': False,
            'note': f'⚠️ XOR variable ({percentage:.1f}% = 0x{most_common_xor:X})'
        })

# Mostrar resultats
print(f"\n{'House':>6} | {'Punts comuns':>13} | {'XOR':>5} | {'Estat':>10} | {'Notes':>30}")
print("-"*80)

constant_xor_houses = []
variable_xor_houses = []
insufficient_data = []

for r in sorted(results, key=lambda x: x['house']):
    xor_str = f"0x{r['xor']:X}" if r['xor'] is not None else "N/A"
    status = "CONSTANT" if r['constant'] else "VARIABLE" if r['xor'] is not None else "INSUF"
    
    print(f"{r['house']:6} | {r['common']:13} | {xor_str:>5} | {status:>10} | {r['note']:>30}")
    
    if r['constant']:
        constant_xor_houses.append((r['house'], r['xor'], r['common']))
    elif r['xor'] is not None:
        variable_xor_houses.append((r['house'], r['xor'], r['common']))
    else:
        insufficient_data.append(r['house'])

# Resum final
print("\n" + "="*80)
print("RESUM FINAL")
print("="*80)

print(f"\n✅ Houses amb XOR CONSTANT (incloent base 247): {len(constant_xor_houses) + 1}")
if constant_xor_houses:
    print("   Houses:")
    print(f"   - {base_house} (base)")
    for house, xor, n in constant_xor_houses:
        print(f"   - {house} (XOR 0x{xor:X}, n={n})")

print(f"\n⚠️ Houses amb XOR VARIABLE: {len(variable_xor_houses)}")
if variable_xor_houses:
    for house, xor, n in variable_xor_houses:
        print(f"   - {house} (XOR més comú: 0x{xor:X}, n={n})")

print(f"\n❌ Houses amb dades insuficients: {len(insufficient_data)}")
if insufficient_data:
    print(f"   {insufficient_data}")

# Conclusió
print("\n" + "="*80)
print("CONCLUSIÓ")
print("="*80)

total_houses = len(captures_by_house)
universal_houses = len(constant_xor_houses) + 1  # +1 per base

if universal_houses == total_houses:
    print("\n🎉 GENERADOR COMPLETAMENT UNIVERSAL!")
    print(f"   Tots els {total_houses} House IDs usen transformacions XOR constants")
    print("   El generador pot funcionar per QUALSEVOL House ID")
elif universal_houses / total_houses >= 0.8:
    print(f"\n✅ GENERADOR QUASI-UNIVERSAL")
    print(f"   {universal_houses}/{total_houses} Houses ({universal_houses/total_houses*100:.1f}%) amb XOR constant")
    print(f"   Cobertura suficient per considerar-lo universal")
else:
    print(f"\n⚠️ GENERADOR PARCIAL")
    print(f"   Només {universal_houses}/{total_houses} Houses ({universal_houses/total_houses*100:.1f}%) amb XOR constant")
    print(f"   Necessita més investigació o múltiples LUTs")

# Guardar resultats
with open('all_houses_analysis.txt', 'w') as f:
    f.write("ANÀLISI COMPLET DE TOTS ELS HOUSE IDs\n")
    f.write("="*80 + "\n\n")
    
    f.write(f"Total Houses: {total_houses}\n")
    f.write(f"Houses amb XOR constant: {universal_houses}\n\n")
    
    f.write("Houses amb XOR constant:\n")
    f.write(f"  {base_house} (base)\n")
    for house, xor, n in constant_xor_houses:
        f.write(f"  {house} (XOR 0x{xor:X}, n={n})\n")
    
    if variable_xor_houses:
        f.write("\nHouses amb XOR variable:\n")
        for house, xor, n in variable_xor_houses:
            f.write(f"  {house} (XOR més comú: 0x{xor:X}, n={n})\n")

print(f"\n✅ Resultats guardats a: all_houses_analysis.txt")
