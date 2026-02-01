#!/usr/bin/env python3
"""
Extreu la LUT P de 'tramas_thn132n.csv' (House 247).
Verifica el checksum per identificar quina posició és P.
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
TRAMAS_FILE = BASE_DIR / "tramas_thn132n.csv"

def get_nibbles(hex_str):
    return [int(c, 16) for c in hex_str]

def extract_lut_from_tramas():
    print(f"Processant {TRAMAS_FILE}...")
    
    p_map = {}
    
    with open(TRAMAS_FILE, 'r') as f:
        # No header? Looks like: -20.0,247,1,HEX,RAW
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 4: continue
            
            try:
                temp_c = float(row[0])
                house = int(row[1])
                hex_str = row[3]
                
                if house != 247: continue
                
                # Hex: EC4017F2002814A1
                # Nibbles: E C 4 0 1 7 F 2 0 0 2 8 1 4 A 1
                nibbles = get_nibbles(hex_str)
                
                # Checksum calc (Sum of first 12 nibbles)
                # Payload: 0..11
                payload = nibbles[:12]
                s = sum(payload)
                chk_val = s & 0xFF
                chk_hi = (chk_val >> 4) & 0xF
                chk_lo = chk_val & 0xF
                
                # Expected Checksum Nibbles: chk_lo, chk_hi
                # In hex string: nibbles[12], nibbles[13]
                
                r1_actual = nibbles[12]
                m_actual = nibbles[13]
                
                if r1_actual == chk_lo and m_actual == chk_hi:
                    # Checksum OK!
                    # P is likely the next nibble (14)
                    p = nibbles[14]
                    
                    # Temp Index
                    t_idx = int(round((temp_c + 40) * 10))
                    p_map[t_idx] = p
                else:
                    # print(f"Checksum mismatch: Calc {chk_lo:X}{chk_hi:X} vs Act {r1_actual:X}{m_actual:X}")
                    pass
                    
            except ValueError:
                continue
                
    print(f"  ✅ Extrets {len(p_map)} valors P per House 247.")
    
    # Generate C++ Code
    print("\n  // P_TABLE for House 247 (0xF7)")
    print("  const uint8_t P_TABLE_HOUSE_247[] = {")
    
    min_t = min(p_map.keys())
    max_t = max(p_map.keys())
    print(f"  // Temp Range: {(min_t/10)-40:.1f}C to {(max_t/10)-40:.1f}C")
    
    # Output array (indexed by TempIdx relative to start? Or full 0-900?)
    # Let's output full 0..900 range for safety, filling unknown with 0
    
    line = "    "
    for t in range(0, 901):
        val = p_map.get(t, 0)
        line += f"0x{val:X}, "
        if len(line) > 70:
            print(line)
            line = "    "
    print(line)
    print("  };")

if __name__ == "__main__":
    extract_lut_from_tramas()
