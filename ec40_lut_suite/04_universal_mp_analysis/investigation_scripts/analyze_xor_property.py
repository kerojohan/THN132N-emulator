#!/usr/bin/env python3
"""
Analitza la propietat matemàtica de l'algorisme XOR que fa que
qualsevol valor afegit sigui auto-consistent.
"""

def xor_shift_accumulate(nibbles):
    """L'algorisme que estem utilitzant."""
    h = 0
    for nib in nibbles:
        h = ((h << 4) ^ nib) & 0xFF
    return h & 0xF

# Test amb diferents seqüències
test_nibbles = [0xE, 0xC, 0x4, 0x0, 0x1, 0x3, 0x0, 0x2, 0x9, 0x4, 0x1, 0x0, 0x2, 0x3]

print("Analitzant propietat matemàtica:\n")
print(f"Nibbles base (14): {[f'{n:X}' for n in test_nibbles]}")

base_result = xor_shift_accumulate(test_nibbles)
print(f"XOR acumulat: {base_result:X}\n")

print("Provant afegir cada nibble 0-F:")
for add_nib in range(16):
    extended = test_nibbles + [add_nib]
    result = xor_shift_accumulate(extended)
    
    # Què hauria de passar matemàticament?
    # h_14 = resultat després de 14 nibbles
    # Afegir nibble N:
    #   h_15 = (((h_14 << 4) ^ N) & 0xFF) & 0xF
    #   h_15 = ((h_14 << 4) & 0xFF) ^ N) & 0xF
    
    # Calculem manualment
    h_14_full = 0
    for nib in test_nibbles:
        h_14_full = ((h_14_full << 4) ^ nib) & 0xFF
    
    # Afegir add_nib
    h_15_manual = ((h_14_full << 4) ^ add_nib) & 0xFF
    h_15_low = h_15_manual & 0xF
    
    print(f"  +{add_nib:X}: result={result:X}, manual={(h_14_full<<4)&0xFF:02X}^{add_nib:X}={h_15_manual:02X} -> {h_15_low:X}")
    
# Ara entenc: quan fem << 4 sobre h_14 (que és 0x?3), obtenim 0x30
# Després XOR amb el nibble afegit
print(f"\nPer tant:")
print(f"  h_14 = 0x{h_14_full:02X}")
print(f"  h_14 << 4 = 0x{(h_14_full << 4) & 0xFF:02X}")
print(f"  (h_14 << 4) ^ N dona el nibble baix = N quan (h_14 << 4) & 0xF == 0")
print(f"  Però (0x{h_14_full:02X} << 4) & 0xFF = 0x{(h_14_full << 4) & 0xFF:02X}")
print(f"  El nibble baix és: {((h_14_full << 4) & 0xFF) & 0xF:X}")

print(f"\n🔍 Ah! El truc és que (h_14 << 4) & 0xFF elimina els bits alts.")
print(f"   Si h_14 = 0x{h_14_full:02X}, aleshores:")
print(f"   (0x{h_14_full:02X} << 4) = 0x{h_14_full << 4:04X}")
print(f"   (0x{h_14_full << 4:04X}) & 0xFF = 0x{(h_14_full << 4) & 0xFF:02X}")
print(f"   0x{(h_14_full << 4) & 0xFF:02X} ^ N, el nibble baix depèn de 0x{((h_14_full << 4) & 0xFF) & 0xF:X} ^ N")

base_low = ((h_14_full << 4) & 0xFF) & 0xF
print(f"\n   Base nibble baix: 0x{base_low:X}")
print(f"   Per tant: result = 0x{base_low:X} ^ N")
print(f"   Per N=9: result = 0x{base_low:X} ^ 0x9 = 0x{base_low ^ 0x9:X}")
