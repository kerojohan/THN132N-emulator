#!/usr/bin/env python3
"""
Intenta trobar l'algoritme que genera els valors de la M_TABLE.
Input: House 0xF7, Temp.
Target: Baix 8 bits de M_TABLE (ex: 0xA1 per T=-16).
"""

M_TABLE_SUBSET = [
    (-16, 0x2A1), (-15, 0x252), (-14, 0x203), (-13, 0x2B5),
    (-12, 0x2E4), (-11, 0x217), (-10, 0x246), (-9, 0x29A)
]

def crc8(data, poly, init, xor_out):
    crc = init
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
        crc &= 0xFF
    return crc ^ xor_out

def solve_gen():
    print("Buscant generador M_TABLE...")
    
    # Preparar dades
    # Input bytes: House, Temp?
    # House 0xF7. Temp -16 (0xF0? 0xE0? 160?).
    # Provem diferents codificacions de Temp.
    
    candidates = []
    for t, val in M_TABLE_SUBSET:
        target = val & 0xFF # 0xA1
        
        # Temp encodings
        # 1. Signed byte: -16 -> 0xF0
        # 2. Offset 40: -16+40 = 24 -> 0x18
        # 3. BCD: 16 -> 0x16 (negatiu?)
        # 4. Abs BCD: 16 -> 0x16.
        
        t_bytes_list = [
            [0xF7, t & 0xFF],           # House, SignedTemp
            [0xF7, (t+40) & 0xFF],      # House, OffsetTemp
            [0xF7, abs(t)],             # House, AbsTemp
            [(t+40) & 0xFF, 0xF7],      # Swap order
        ]
        
        candidates.append((t_bytes_list, target))
        
    # Brute force CRC-8
    for poly in range(256):
        for init in range(256):
            for xor_out in [0]: # Simplificació
                
                # Check encoding 1
                matches = 0
                for t_bytes_list, target in candidates:
                    # Provem cada encoding
                    found = False
                    for b in t_bytes_list:
                        if crc8(b, poly, init, xor_out) == target:
                            found = True
                            break
                    if found: matches += 1
                    
                if matches == len(candidates):
                    print(f"✨ TROBAT! CRC-8 Poly=0x{poly:X}, Init=0x{init:X}")
                    return

    print("No s'ha trobat amb CRC-8 simple.")

if __name__ == "__main__":
    solve_gen()
