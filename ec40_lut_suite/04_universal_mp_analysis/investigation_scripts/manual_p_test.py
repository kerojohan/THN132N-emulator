#!/usr/bin/env python3
"""
Test manual detailed del càlcul de P per entendre exactament què passa.
"""

# Exemple: ec4013029410239e
nibbles_captured = [0xE, 0xC, 0x4, 0x0, 0x1, 0x3, 0x0, 0x2, 0x9, 0x4, 0x1, 0x0, 0x2, 0x3, 0x9, 0xE]

print("Nibbles capturats:") 
print(f"  {[f'{n:X}' for n in nibbles_captured]}")
print(f"  Posicions: {list(range(16))}\n")

# Calcular P sobre diferents rangs
def calc_p(nibbles):
    h = 0
    for nib in nibbles:
        h = ((h << 4) ^ nib) & 0xFF
    return h & 0xF

# Test sobre [0:15]
p_015 = calc_p(nibbles_captured[0:15])
print(f"P calculat sobre [0:15]: {p_015:X}")
print( f"P real (pos 14):         {nibbles_captured[14]:X}")
print(f"Match: {p_015 == nibbles_captured[14]}\n")

# Ara provar l'algorisme "auto-consistent"
nibbles_14 = nibbles_captured[0:14]

print("Provant auto-consistency:")
for p_test in range(16):
    nibbles_15_test = nibbles_14 + [p_test]
    p_calc = calc_p(nibbles_15_test)
    
    if p_calc == p_test:
        status = "✓" if p_test == nibbles_captured[14] else "✗"
        print(f"{status} P={p_test:X}: calc_p([...14..., {p_test:X}]) = {p_calc:X} (auto-consistent)")
    
print(f"\nP real és: {nibbles_captured[14]:X}")

# Verificar què dóna calc_p sobre [0:15] real
print(f"\nVerificació final:")
print(f"calc_p(nibbles[0:15]) = calc_p({[f'{n:X}' for n in nibbles_captured[0:15]]}) = {calc_p(nibbles_captured[0:15]):X}")
