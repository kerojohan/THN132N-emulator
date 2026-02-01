#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Análisis del patrón XOR = 0x075 entre Houses 3 y 247
Este es un HALLAZGO CRÍTICO que sugiere una derivación simple de tablas P
"""

# Tablas P encontradas
P_HOUSE_3 = [0x075, 0x000, 0x09F, 0x0EA, 0x0C0, 0x0B5, 0x02A, 0x05F, 0x01E, 0x06B]
P_HOUSE_247 = [0x000, 0x075, 0x0EA, 0x09F, 0x0B5, 0x0C0, 0x05F, 0x02A, 0x06B, 0x01E]
P_HOUSE_96 = [0x01E, 0x01E, 0x0F4, 0x081, 0x0DE, 0x0DE, 0x034, 0x034, 0x000, 0x000]

print("="*80)
print("ANÁLISIS DEL PATRÓN XOR = 0x075 ENTRE HOUSES 3 Y 247")
print("="*80)

# Verificar XOR
print("\n1. Verificación del XOR constante:")
print("-"*80)
xor_values = []
for i in range(10):
    xor_val = P_HOUSE_3[i] ^ P_HOUSE_247[i]
    xor_values.append(xor_val)
    print(f"  Décima {i}: 0x{P_HOUSE_3[i]:03X} ^ 0x{P_HOUSE_247[i]:03X} = 0x{xor_val:03X}")

if len(set(xor_values)) == 1:
    print(f"\n✓ ¡CONFIRMADO! XOR constante = 0x{xor_values[0]:03X}")
else:
    print(f"\n✗ XOR NO constante: {set(xor_values)}")

# Análisis de house codes
print("\n2. Análisis de los House Codes:")
print("-"*80)
print(f"  House 3:   0x{3:02X} = {3:08b}")
print(f"  House 247: 0x{247:02X} = {247:08b}")
print(f"  XOR:       0x{3^247:02X} = {3^247:08b}")

# ¿Está relacionado el XOR de houses con el XOR de tablas?
house_xor = 3 ^ 247
table_xor = 0x075

print(f"\n  House XOR = 0x{house_xor:02X} ({house_xor})")
print(f"  Table XOR = 0x{table_xor:03X} ({table_xor})")

if house_xor == table_xor:
    print("  ✓ ¡Son iguales!")
elif (house_xor << 8) | house_xor == table_xor:
    print("  ✓ Table XOR = House XOR repetido")
else:
    # Buscar otras relaciones
    print(f"\n  Relaciones posibles:")
    print(f"    House XOR * 2 = 0x{house_xor*2:03X}")
    print(f"    House XOR << 4 = 0x{(house_xor << 4) & 0xFFF:03X}")
    
    # Nibbles del house XOR
    h_high = (house_xor >> 4) & 0x0F
    h_low = house_xor & 0x0F
    print(f"    House XOR nibble alto = 0x{h_high:X}")
    print(f"    House XOR nibble bajo  = 0x{h_low:X}")
    
    # ¿Coincide con algún nibble de la tabla XOR?
    t_high = (table_xor >> 8) & 0x0F
    t_mid = (table_xor >> 4) & 0x0F
    t_low = table_xor & 0x0F
    print(f"    Table XOR nibbles: 0x{t_high:X}, 0x{t_mid:X}, 0x{t_low:X}")

# Análisis de rotación/permutación
print("\n3. ¿Es la tabla de House 247 una permutación de House 3?")
print("-"*80)

# Ordenar ambas tablas y comparar
sorted_3 = sorted(P_HOUSE_3)
sorted_247 = sorted(P_HOUSE_247)

print(f"  House 3 ordenada:   {[f'0x{x:03X}' for x in sorted_3]}")
print(f"  House 247 ordenada: {[f'0x{x:03X}' for x in sorted_247]}")

if sorted_3 == sorted_247:
    print("  ✓ ¡Contienen los MISMOS valores! Solo están reordenados/rotados.")
    
    # Buscar el patrón de reordenamiento
    print("\n  Buscando patrón de rotación...")
    for offset in range(10):
        match = True
        for i in range(10):
            if P_HOUSE_247[i] != P_HOUSE_3[(i + offset) % 10]:
                match = False
                break
        if match:
            print(f"    ✓ House 247 = House 3 rotada {offset} posiciones a la izquierda")
    
    # Buscar permutaciones específicas
    print("\n  Mapeando posiciones:")
    for i in range(10):
        try:
            original_pos = P_HOUSE_3.index(P_HOUSE_247[i])
            print(f"    247[{i}] = 3[{original_pos}]  (valor 0x{P_HOUSE_247[i]:03X})")
        except ValueError:
            print(f"    247[{i}] no encontrado en House 3")
else:
    print("  ✗ Las tablas NO contienen los mismos valores.")

# Comparar con House 96
print("\n4. Comparación con House 96:")
print("-"*80)
print(f"  House 96: {[f'0x{x:03X}' for x in P_HOUSE_96]}")

# ¿House 96 tiene XOR constante con House 3?
xor_96_3 = []
for i in range(10):
    xor_val = P_HOUSE_3[i] ^ P_HOUSE_96[i]
    xor_96_3.append(xor_val)

unique_xors = set(xor_96_3)
print(f"\n  XORs entre House 3 y 96: {len(unique_xors)} valores únicos")
if len(unique_xors) <= 3:
    print(f"    Valores: {[f'0x{x:03X}' for x in sorted(unique_xors)]}")

# Resumen
print("\n" + "="*80)
print("CONCLUSIONES:")
print("="*80)
print("\n✓ House 3 y 247 tienen un XOR constante de 0x075 en sus tablas P")
print("✓ Esto sugiere que la tabla P puede derivarse aplicando XOR")
print("✓ Las tablas contienen los mismos valores, solo reordenados")
print("\nPróximos pasos:")
print("  - Verificar si otras combinaciones de houses tienen XOR constante")
print("  - Determinar la función de transformación exacta")
print("  - Probar si esto funciona para la tabla M también")
