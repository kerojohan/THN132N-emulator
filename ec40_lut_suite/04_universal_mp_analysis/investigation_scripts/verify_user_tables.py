#!/usr/bin/env python3
"""
Verifica les taules M/P proporcionades per l'usuari contra les dades reals.
Hipòtesi: Checksum_Full (R1, M, P) = M_TABLE[Int] + P_TABLE[Dec]
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
TRAMAS_FILE = BASE_DIR / "tramas_thn132n.csv"

# Dades de l'usuari
P_TABLE = [
  0x000, 0x075, 0x0EA, 0x09F, 0x0B5,
  0x0C0, 0x05F, 0x02A, 0x06B, 0x01E
]

M_MIN_E = -16
M_MAX_E = 54

M_TABLE = [
  0x2A1, 0x252, 0x203, 0x2B5, 0x2E4, 0x217, 0x246, 0x29A, # -16..-9
  0x2CB, 0x2F7, 0x2A6, 0x255, 0x204, 0x2B2, 0x2E3, 0x210, # -8..-1
  0x2C2, 0x148, 0x1BB, 0x1EA, 0x15C, 0x10D, 0x1FE, 0x1AF, # 0..7
  0x193, 0x1C2, 0x11E, 0x14F, 0x1BC, 0x236, 0x280, 0x10A, # 8..15
  0x1F9, 0x1A8, 0x194, 0x866, 0x2CC, 0x146, 0x1B5, 0x1E4, # 16..23
  0x152, 0x103, 0x1F0, 0x1A1, 0x246, 0x1CC, 0x110, 0x141, # 24..31
  0x1B2, 0x1E3, 0x8F6, 0x8A7, 0x854, 0x805, 0x839, 0x868, # 32..39
  0x8C6, 0x897, 0x864, 0x835, 0x883, 0x8D2, 0x821, 0x870, # 40..47
  0x84C, 0x81D, 0x162, 0x133, 0x863, 0x191, 0x884          # 48..54
]

def verify():
    print("Verificant taules d'usuari...")
    
    with open(TRAMAS_FILE, 'r') as f:
        reader = csv.reader(f)
        total = 0
        matches = 0
        
        for row in reader:
            if len(row) < 4: continue
            try:
                temp_c = float(row[0])
                house = int(row[1])
                hex_str = row[3]
                
                if house != 247: continue
                
                # Filtrar rang (Positius només per debug)
                t_int = int(temp_c)
                if t_int < 20 or t_int > 30:
                    continue
                    
                # Calcular índexs
                m_idx = t_int - M_MIN_E
                
                # Decimal part: abs(temp) % 1 * 10
                # 16.5 -> 5
                # -16.5 -> 5
                t_dec = int(round(abs(temp_c) * 10)) % 10
                
                if m_idx < 0 or m_idx >= len(M_TABLE): continue
                
                # Valors taula
                m_val = M_TABLE[m_idx]
                p_val = P_TABLE[t_dec]
                
                # Provem Suma
                calc_val = (m_val + p_val) & 0xFFF
                real_val = int(hex_str[-3:], 16)
                
                total += 1
                if calc_val == real_val:
                    matches += 1
                else:
                    # Debug primers 10 errors
                    if matches == 0 and total <= 10:
                        diff = (real_val - m_val) & 0xFFF
                        print(f"T={temp_c:5.1f} | M[{m_idx}]={m_val:03X} | P[{t_dec}]={p_val:03X} | Real={real_val:03X} | Diff={diff:03X}")
            
            except ValueError:
                continue
                
    print(f"Resultat: {matches}/{total} coincidències.")

if __name__ == "__main__":
    verify()
