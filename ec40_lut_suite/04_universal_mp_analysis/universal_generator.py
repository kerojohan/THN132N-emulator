#!/usr/bin/env python3
"""
Generador Universal de Trames i Checksum (M/P) per Oregon Scientific THN132N.
Basat en l'algoritme de Suma de Nibbles descobert.
"""

def to_nibbles(val, count):
    """Converteix enter a llista de n nibbles (Little Endian per bytes, però nibbles?)"""
    # Oregon sembla usar LSN first dins del byte per alguns camps
    # Però per la suma, sembla que agafem els nibbles tal qual apareixen al raw
    nibbles = []
    for _ in range(count):
        nibbles.append(val & 0xF)
        val >>= 4
    return list(reversed(nibbles)) # Big endian per defecte?

def generate_message(house_code, channel, temp_c):
    """
    Genera els nibbles del missatge i calcula el checksum.
    """
    # ID: EC40 (Fixed) -> E C 4 0
    nibbles = [0xE, 0xC, 0x4, 0x0]
    
    # Channel: 1 nibble
    nibbles.append(channel & 0xF)
    
    # House Code: 2 nibbles (0xAD -> D, A)
    # Al raw veiem D, A. Això és 0xAD amb nibbles invertits?
    # House 173 = 0xAD. Raw té ...1 D A...
    # Sembla que House Code s'envia LSN, MSN.
    h_lsn = house_code & 0xF
    h_msn = (house_code >> 4) & 0xF
    nibbles.append(h_lsn)
    nibbles.append(h_msn)
    
    # Nibble 7: Unknown/Fixed?
    # Observed as '2' in all samples for House 173.
    # Could be battery/flags.
    nibbles.append(0x2)
    
    # Temp: 3 nibbles. 18.1 -> 1, 8, 1.
    # Format: LSD, Middle, MSD?
    # 18.1 -> 181. Nibbles: 1, 8, 1.
    # Raw té ...1 8 1...
    # Sembla LSN, Middle, MSN del valor en dècimes?
    # 18.1 * 10 = 181 (0xB5). Hex no quadra.
    # És BCD! 1 8 1.
    # 18.1 -> 1, 8, 1.
    # Signe? THN132N suporta negatius?
    # Assumim positiu per ara.
    t_val = int(abs(temp_c) * 10)
    t_lsn = t_val % 10
    t_mid = (t_val // 10) % 10
    t_msn = (t_val // 100) % 10
    
    # Raw order: 1, 8, 1 (LSD, Mid, MSD)
    nibbles.append(t_lsn)
    nibbles.append(t_mid)
    nibbles.append(t_msn)
    
    # Flags/Battery?
    # Raw té ...1 0... després de temp?
    # Line 1: ...1 8 1 0...
    # Line 2: ...1 8 1 0...
    # Sembla que hi ha un nibble 0 o flags.
    # Assumim 0 per defecte.
    nibbles.append(0)
    
    # Checksum Calculation
    # Sum of all nibbles
    total_sum = sum(nibbles)
    
    # Checksum byte = Swap(Sum & 0xFF)
    # Ex: Sum 0x42 -> Checksum 0x24
    sum_byte = total_sum & 0xFF
    chk_hi = (sum_byte >> 4) & 0xF
    chk_lo = sum_byte & 0xF
    
    # Checksum nibbles en ordre: chk_lo, chk_hi
    # Raw: ...2 4... (on sum was 0x42)
    # So append chk_lo, then chk_hi
    nibbles.append(chk_lo)
    nibbles.append(chk_hi)
    
    return nibbles, total_sum

def main():
    print("Generador Universal Oregon Scientific THN132N")
    print("===========================================")
    
    # Test Case 1: House 173, Temp 18.1
    # Raw: E C 4 0 1 D A 2 1 8 1 0 [2 4 3]
    h = 173
    t = 18.1
    c = 1
    
    print(f"\nTest: House {h}, Temp {t}C")
    nibbles, s = generate_message(h, c, t)
    
    print(f"Nibbles generats: {[hex(n)[2:] for n in nibbles]}")
    print(f"Suma: 0x{s:X}")
    
    # M és el segon nibble del checksum (chk_hi)
    # R1 és el primer (chk_lo)
    r1 = nibbles[-2]
    m = nibbles[-1]
    
    print(f"Calculat: R1={r1:X}, M={m:X}")
    print(f"Esperat (CSV): R1=2, M=4")
    
    if r1 == 2 and m == 4:
        print("✅ ÈXIT! El càlcul coincideix.")
    else:
        print("❌ FALLADA.")

if __name__ == "__main__":
    main()
