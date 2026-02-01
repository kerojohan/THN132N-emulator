#!/usr/bin/env python3
"""
Intenta trobar la lògica que genera la M_TABLE proporcionada per l'usuari.
Input: House 247, Temp -16..54.
Output: Valors M_TABLE.
"""

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

def solve_logic():
    house = 247
    
    print("Analitzant M_TABLE...")
    
    # 1. Analitzar diferències entre valors consecutius
    diffs = []
    for i in range(len(M_TABLE)-1):
        d = (M_TABLE[i+1] - M_TABLE[i]) & 0xFFF
        diffs.append(d)
        
    print(f"Diferències (primers 10): {[hex(d) for d in diffs[:10]]}")
    
    # 2. Buscar patró en els nibbles
    # Nibble 0 (Low), 1 (Mid), 2 (High)
    n0 = [x & 0xF for x in M_TABLE]
    n1 = [(x >> 4) & 0xF for x in M_TABLE]
    n2 = [(x >> 8) & 0xF for x in M_TABLE]
    
    print(f"Nibble 2 (High): {n2[:20]}...")
    print(f"Nibble 1 (Mid):  {n1[:20]}...")
    print(f"Nibble 0 (Low):  {n0[:20]}...")
    
    # 3. Relacionar amb Suma de Nibbles (Universal Generator)
    # Temp -16 -> Nibbles 0, 6, 1 (LSN, Mid, MSN)? No, 16.0 -> 160 -> 0, 6, 1.
    # Signe?
    # House 247 -> 7, F.
    
    # Provem de generar la suma per cada temperatura i veure la relació
    print("\nComparant amb Suma Universal:")
    for i, val in enumerate(M_TABLE):
        temp = -16 + i
        
        # Generar nibbles temp (assumint format BCD positiu + signe?)
        # O offset?
        # Oregon v2.1 sol usar offset +40C? No, THN132N envia signe.
        # Però el generador universal que vaig fer usava abs(temp).
        
        # Provem format: LSN, Mid, MSN de abs(temp)
        t_abs = abs(temp)
        t_val = int(t_abs * 10) # .0
        t0 = t_val % 10
        t1 = (t_val // 10) % 10
        t2 = (t_val // 100) % 10
        
        # Suma parcial (House + Temp)
        # House 247 -> 7 + 15 = 22
        # Temp -> t0 + t1 + t2
        # Fixed -> ?
        
        s = 7 + 15 + t0 + t1 + t2
        
        # Checksum = Swap(s)
        chk = ((s & 0xF) << 4) | ((s >> 4) & 0xF)
        
        # Comparem chk amb els nibbles de M_TABLE
        # M_TABLE té 3 nibbles.
        # Potser M_TABLE = (R1, M, P)?
        # Val = 0x2A1. R1=2, M=A, P=1.
        
        # Si chk fos R1, M.
        # R1 = s & 0xF. M = s >> 4.
        # Per T=-16 (160 -> 0+6+1=7). Sum = 22+7 = 29 (0x1D).
        # R1=D, M=1.
        # User: R1=2, M=A.
        # Diff: 2-D = -11 (5). A-1 = 9.
        
        if i < 5:
            print(f"T={temp}: Sum={s} (0x{s:X}) -> R1={s&0xF:X}, M={s>>4:X}. User: {val:03X}")

if __name__ == "__main__":
    solve_logic()
