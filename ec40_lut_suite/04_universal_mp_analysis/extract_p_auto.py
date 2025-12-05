#!/usr/bin/env python3
"""
Extractora Automàtica de LUTs P per qualsevol House ID.
Solució pràctica quan no existeix fórmula universal.
"""

import csv
import sys
from pathlib import Path
from collections import defaultdict

def extract_p_lut(csv_file, house_id, output_file=None):
    """
    Extreu la taula P per un House ID donat des d'un fitxer CSV.
    
    Args:
        csv_file: Path al CSV (format: temp, house, channel, hex, raw)
        house_id: House Code a extreure (ex: 247)
        output_file: Path de sortida per al .h (opcional)
    """
    p_map = {}
    
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 4: continue
            
            try:
                temp_c = float(row[0])
                house = int(row[1])
                hex_str = row[3]
                
                if house != house_id: continue
                
                # Calcular checksum per validar
                nibbles = [int(c, 16) for c in hex_str[:12]]
                s = sum(nibbles)
                chk_lo = s & 0xF
                chk_hi = (s >> 4) & 0xF
                
                r1_actual = int(hex_str[12], 16)
                m_actual = int(hex_str[13], 16)
                
                if r1_actual == chk_lo and m_actual == chk_hi:
                    # Checksum OK, P és el següent nibble
                    p = int(hex_str[14], 16)
                    t_idx = int(round((temp_c + 40) * 10))
                    p_map[t_idx] = p
                    
            except (ValueError, IndexError):
                continue
                
    if not p_map:
        print(f"❌ No s'han trobat dades validades per House {house_id}.")
        return None
        
    print(f"✅ Extrets {len(p_map)} valors P per House {house_id} (0x{house_id:X}).")
    
    # Estadístiques
    temps = sorted(p_map.keys())
    min_t = (temps[0] / 10.0) - 40.0
    max_t = (temps[-1] / 10.0) - 40.0
    print(f"   Rang Temperatura: {min_t:.1f}°C a {max_t:.1f}°C")
    
    # Generar codi C++
    if output_file:
        with open(output_file, 'w') as f:
            f.write(f"// P_TABLE for House {house_id} (0x{house_id:X})\n")
            f.write(f"// Auto-generated. Temp range: {min_t:.1f}C to {max_t:.1f}C\n")
            f.write(f"// Index = (Temp_C + 40) * 10\n\n")
            f.write(f"const uint8_t P_TABLE_HOUSE_{house_id}[] = {{\n")
            
            line = "    "
            for t in range(0, 901):
                val = p_map.get(t, 0)
                line += f"0x{val:X}, "
                if len(line) > 70:
                    f.write(line + "\n")
                    line = "    "
            f.write(line + "\n};\n")
            
        print(f"   Guardat a: {output_file}")
    
    return p_map

def main():
    if len(sys.argv) < 3:
        print("Ús: python3 extract_p_auto.py <csv_file> <house_id> [output.h]")
        print("Ex: python3 extract_p_auto.py tramas_thn132n.csv 247 oregon_p_247.h")
        sys.exit(1)
        
    csv_file = sys.argv[1]
    house_id = int(sys.argv[2])
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    extract_p_lut(csv_file, house_id, output_file)

if __name__ == "__main__":
    main()
