#!/usr/bin/env python3
"""
Analitza el patró entre parells de house codes amb taula M idèntica (M XOR = 0)
"""

# Parells coneguts amb M XOR = 0
pairs_with_same_M = [
    (3, 247),    # Del teu estudi anterior
    (95, 187),   # Descobert avui
]

print("="*70)
print("ANÀLISI DE PARELLS AMB TAULA M IDÈNTICA (M XOR = 0)")
print("="*70)

for h1, h2 in pairs_with_same_M:
    house_xor = h1 ^ h2
    
    print(f"\nHouse {h1} vs House {h2}:")
    print(f"  Decimal: {h1} vs {h2}")
    print(f"  Hexadecimal: 0x{h1:02X} vs 0x{h2:02X}")
    print(f"  Binari: 0b{h1:08b} vs 0b{h2:08b}")
    print(f"  House XOR: 0x{house_xor:02X} = {house_xor} = 0b{house_xor:08b}")
    
    # Analitzar bits individuals
    print(f"\n  Anàlisi de bits:")
    for bit in range(8):
        bit1 = (h1 >> bit) & 1
        bit2 = (h2 >> bit) & 1
        xor_bit = bit1 ^ bit2
        print(f"    Bit {bit}: {bit1} XOR {bit2} = {xor_bit}")

print("\n" + "="*70)
print("COMPARACIÓ DELS XORs")
print("="*70)

xor1 = pairs_with_same_M[0][0] ^ pairs_with_same_M[0][1]
xor2 = pairs_with_same_M[1][0] ^ pairs_with_same_M[1][1]

print(f"\nHouse 3 XOR 247 = 0x{xor1:02X} = {xor1:3d} = 0b{xor1:08b}")
print(f"House 95 XOR 187 = 0x{xor2:02X} = {xor2:3d} = 0b{xor2:08b}")
print(f"XOR dels XORs    = 0x{xor1^xor2:02X} = {xor1^xor2:3d} = 0b{xor1^xor2:08b}")

# Buscar patrons en els XORs
print("\n" + "="*70)
print("PATRONS DETECTATS")
print("="*70)

# Nibbles (4 bits baixos i 4 bits alts)
print(f"\n0x{xor1:02X}:")
print(f"  Nibble alt (bits 7-4): 0x{(xor1 >> 4):X} = {(xor1 >> 4):2d} = 0b{(xor1 >> 4):04b}")
print(f"  Nibble baix (bits 3-0): 0x{(xor1 & 0xF):X} = {(xor1 & 0xF):2d} = 0b{(xor1 & 0xF):04b}")

print(f"\n0x{xor2:02X}:")
print(f"  Nibble alt (bits 7-4): 0x{(xor2 >> 4):X} = {(xor2 >> 4):2d} = 0b{(xor2 >> 4):04b}")
print(f"  Nibble baix (bits 3-0): 0x{(xor2 & 0xF):X} = {(xor2 & 0xF):2d} = 0b{(xor2 & 0xF):04b}")

# Comprovar si comparteixen nibble baix
if (xor1 & 0xF) == (xor2 & 0xF):
    print(f"\n✨ PATRÓ TROBAT: Ambdós XORs tenen el mateix nibble baix: 0x{xor1 & 0xF:X}")

# Comprovar bits específics
print("\n" + "="*70)
print("BITS COMUNS EN ELS XORs")
print("="*70)

common_bits = []
for bit in range(8):
    bit1 = (xor1 >> bit) & 1
    bit2 = (xor2 >> bit) & 1
    if bit1 == bit2 == 1:
        common_bits.append(bit)
        print(f"  Bit {bit}: Ambdós tenen valor 1")

if common_bits:
    print(f"\n✨ Bits comuns activats (=1): {common_bits}")

# Hipòtesi
print("\n" + "="*70)
print("HIPÒTESI")
print("="*70)
print("\nSi dos house codes tenen M XOR = 0 (taula M idèntica),")
print("llavors el seu House XOR podria seguir un patró específic.")
print("\nLes dades suggereixen que:")
if (xor1 & 0xF) == (xor2 & 0xF):
    print(f"- Els 4 bits baixos del House XOR són sempre 0x{xor1 & 0xF:X} = 0b{xor1 & 0xF:04b}")
print(f"- Possiblement hi ha una màscara o condició sobre aquests bits")
print(f"- Cal més dades per confirmar el patró")

print("\n" + "="*70)
print("PROPERA ACCIÓ")
print("="*70)
print("\nPer validar aquesta hipòtesi, caldria:")
print("1. Buscar altres parells amb taula M idèntica entre els house IDs disponibles")
print("2. Comprovar si tots comparteixen el mateix nibble baix en el House XOR")
print("3. Si es confirma, podem predir quins house IDs tindran taula M idèntica")
