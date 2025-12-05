#!/usr/bin/env python3
"""
Creador Universal de Trames M/P per Oregon Scientific THN132N.
Combina:
1. Algoritme Matemàtic Universal per M i R1 (Suma de Nibbles).
2. Taula Empírica (LUT) per P (específica per House Code).
"""

import sys

# Taula P per House 247 (0xF7)
# Extreta de tramas_thn132n.csv
# Index: (Temp_C + 40) * 10. Rang 0..900.
# Per simplificar, posem només els valors coneguts o 0.
# En una implementació real, això estaria en un fitxer .h o base de dades.
P_LUT_247 = {
    # Valors extrets (mostra)
    200: 0x0, # -20.0
    205: 0xC, # -19.5
    210: 0x0, # -19.0
    # ... (La taula completa és gran, aquí simulem la lògica)
}

def get_p_value(house, temp_c):
    """
    Retorna el valor P per a un House i Temp donats.
    Si no tenim taula, retorna 0 (o un valor per defecte).
    """
    # Aquí es podria carregar la LUT completa
    # Per ara, implementem la lògica observada per House 247 si fos possible
    # O simplement retornem un placeholder si no tenim la taula carregada
    
    # Nota: Per House 247, hem vist que P depèn de la temperatura.
    # Si l'usuari vol la taula completa, ja la tenim a 'oregon_p_table_247.h'.
    return 0 # Placeholder

def calculate_checksum(nibbles):
    """
    Calcula el checksum (R1, M) usant Suma de Nibbles.
    """
    total_sum = sum(nibbles)
    
    # Checksum = Swap(Sum & 0xFF)
    s = total_sum & 0xFF
    chk_hi = (s >> 4) & 0xF
    chk_lo = s & 0xF
    
    # R1 és chk_lo, M és chk_hi
    return chk_lo, chk_hi

def generate_frame(house, channel, temp_c):
    """
    Genera la trama completa (nibbles).
    """
    nibbles = []
    
    # 1. ID (EC40) -> E, C, 4, 0
    nibbles.extend([0xE, 0xC, 0x4, 0x0])
    
    # 2. Channel
    nibbles.append(channel & 0xF)
    
    # 3. House Code (LSN, MSN)
    nibbles.append(house & 0xF)
    nibbles.append((house >> 4) & 0xF)
    
    # 4. Fixed Nibble (0x2 per House 247/173)
    # Aquest nibble sembla fix o depèn del House?
    # Per House 173 era 2. Per House 247 també sembla 2.
    nibbles.append(0x2)
    
    # 5. Temp (LSN, Mid, MSN of Abs(Temp*10))
    t_val = int(abs(temp_c) * 10)
    nibbles.append(t_val % 10)
    nibbles.append((t_val // 10) % 10)
    nibbles.append((t_val // 100) % 10)
    
    # 6. Flags/Battery (0x8?)
    # A tramas 247 veiem '8'. A 173 veiem '0'.
    # Això afecta el checksum!
    # Assumim 8 per defecte per 247.
    flags = 0x8 
    nibbles.append(flags)
    
    # 7. Checksum (R1, M)
    r1, m = calculate_checksum(nibbles)
    nibbles.append(r1)
    nibbles.append(m)
    
    # 8. P (Lookup)
    p = get_p_value(house, temp_c)
    nibbles.append(p)
    
    # 9. Final Nibble (Checksum 2?)
    # A tramas veiem un últim nibble '1'?
    # EC4017F2002814A1.
    # 1 4 A 1.
    # R1=1, M=4, P=A. Last=1.
    nibbles.append(0x1) # Placeholder
    
    return nibbles

def main():
    print("Generador Universal de Trames Oregon Scientific")
    print("---------------------------------------------")
    
    # Exemple House 247, Temp 20.0
    h = 247
    t = 20.0
    c = 1
    
    nibbles = generate_frame(h, c, t)
    hex_str = "".join([f"{n:X}" for n in nibbles])
    
    print(f"House: {h}")
    print(f"Temp: {t} C")
    print(f"Trama Generada: {hex_str}")
    print(f"  R1: {nibbles[-4]:X}")
    print(f"  M : {nibbles[-3]:X}")
    print(f"  P : {nibbles[-2]:X} (Placeholder)")

if __name__ == "__main__":
    main()
