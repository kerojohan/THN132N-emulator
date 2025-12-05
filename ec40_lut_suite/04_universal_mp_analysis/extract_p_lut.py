#!/usr/bin/env python3
"""
Extreu la Taula P (LUT) per a un House Code específic.
Aquesta és la solució pràctica quan la fórmula matemàtica és desconeguda.
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "04_universal_mp_analysis" / "golden_master.csv"

def extract_lut(target_house):
    print(f"Extracció LUT P per House {target_house} (0x{target_house:X})...")
    
    p_map = {} # TempIdx -> P
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            h = int(row['house'])
            if h == target_house:
                t = int(row['temp_idx'])
                p = int(row['p'])
                
                # Verificar consistència
                if t in p_map and p_map[t] != p:
                    # Això pot passar si hi ha soroll o si P depèn d'altres coses
                    # Però en general assumim determinisme
                    pass
                p_map[t] = p
                
    if not p_map:
        print("  ❌ No s'han trobat dades per aquest House Code.")
        return

    print(f"  ✅ Trobats {len(p_map)} punts únics.")
    
    # Mostrar la taula ordenada
    sorted_temps = sorted(p_map.keys())
    min_t = sorted_temps[0]
    max_t = sorted_temps[-1]
    
    print(f"  Rang Temp: {(min_t/10)-40:.1f}C a {(max_t/10)-40:.1f}C")
    
    # Generar array C++
    print("\n  // C++ LUT Code")
    print(f"  const uint8_t P_TABLE_HOUSE_{target_house}[] = {{")
    
    # Omplir forats?
    # Per ara mostrem només els valors coneguts o '0' si desconegut
    # Assumim un rang raonable, ex: 0C a 50C (TempIdx 400 a 900)
    
    start_idx = 400 # 0.0 C
    end_idx = 900   # 50.0 C
    
    line = "    "
    for t in range(start_idx, end_idx + 1):
        val = p_map.get(t, 0) # 0 per defecte si falta
        line += f"0x{val:X}, "
        if len(line) > 70:
            print(line)
            line = "    "
    print(line)
    print("  };")

def main():
    # House 247 (Target usuari)
    extract_lut(247)
    
    # House 95 (Referència)
    print("\n" + "-"*40 + "\n")
    extract_lut(95)

if __name__ == "__main__":
    main()
