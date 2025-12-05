#!/usr/bin/env python3
"""
Verifica la Regla Universal de la Taula M:
"La taula M està determinada pels bits 0, 1 i 3 del House Code (ignorant el bit 2 i el nibble alt)."
Això implica que només hi ha 8 taules M possibles.

Agrupa els house codes segons aquesta clau i verifica la consistència interna.
Accepta XOR=7 com a "consistent" si és degut a oscil·lació 3/4 (soroll de sensor).
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent

def load_data():
    CSV_FILES = [
        BASE_DIR / "ec40_live.csv",
        BASE_DIR / "ec40_live_1.csv", 
        BASE_DIR / "ec40_capturas_merged.csv"
    ]
    
    data_by_house = defaultdict(dict)
    
    for csv_file in CSV_FILES:
        if not csv_file.exists():
            continue
        with open(csv_file, 'r') as f:
            for row in csv.DictReader(f):
                try:
                    house = int(row['house_code'])
                    temp = float(row['temp'])
                    
                    checksum_str = row.get('checksum_hex', row.get('R12', ''))
                    r12 = int(checksum_str, 16) if isinstance(checksum_str, str) else int(checksum_str)
                    m = (r12 >> 4) & 0xF
                    
                    if temp not in data_by_house[house]:
                        data_by_house[house][temp] = m
                except:
                    continue
    return data_by_house

def get_m_group(house_code):
    """Retorna l'ID del grup M segons la hipòtesi (bits 0,1,3)"""
    # Màscara 0x0B = 0000 1011 (Bits 0, 1, 3)
    # Ignorem bit 2 (0x04) i bits 4-7 (0xF0)
    return house_code & 0x0B

def check_consistency(houses, data):
    """Comprova la consistència entre tots els parells d'un grup"""
    if len(houses) < 2:
        return "N/A (1 house)"
    
    total_pairs = 0
    consistent_pairs = 0
    details = []
    
    for i, h1 in enumerate(houses):
        for h2 in houses[i+1:]:
            d1 = data.get(h1, {})
            d2 = data.get(h2, {})
            
            common = sorted(set(d1.keys()) & set(d2.keys()))
            if len(common) < 3:
                continue
                
            total_pairs += 1
            xors = set()
            for t in common:
                xors.add(d1[t] ^ d2[t])
            
            # Criteri de consistència relaxat:
            # Consistent si XOR és 0, o si XOR és 7 (degut a 3 vs 4)
            # Si apareix qualsevol altre valor, és inconsistent.
            is_consistent = True
            for x in xors:
                if x != 0 and x != 7:
                    is_consistent = False
                    break
            
            if is_consistent:
                consistent_pairs += 1
                details.append(f"✅ {h1}vs{h2} ({len(common)} pts) XORs:{list(xors)}")
            else:
                details.append(f"❌ {h1}vs{h2} ({len(common)} pts) XORs:{list(xors)}")
    
    if total_pairs == 0:
        return "N/A (no overlap)"
        
    return f"{consistent_pairs}/{total_pairs} consistent. Detalls: {', '.join(details)}"

def main():
    print("="*70)
    print("VERIFICACIÓ DE LA REGLA UNIVERSAL M")
    print("Clau = HouseCode & 0x0B (Bits 0, 1, 3)")
    print("="*70)
    
    data = load_data()
    house_codes = sorted(data.keys())
    
    # Agrupar
    groups = defaultdict(list)
    for h in house_codes:
        key = get_m_group(h)
        groups[key].append(h)
        
    # Verificar cada grup
    for key in sorted(groups.keys()):
        houses = groups[key]
        print(f"\nGRUP M_ID = 0x{key:X} (Bits 0,1,3 = {key:04b})")
        print(f"Houses: {houses} ([{', '.join([f'0x{h:02X}' for h in houses])}])")
        
        result = check_consistency(houses, data)
        print(f"Resultat: {result}")

    print("\n" + "="*70)
    print("RESUM")
    print("="*70)
    print("Si tots els grups mostren consistència (acceptant XOR 7 com a soroll),")
    print("llavors la regla és vàlida i hem reduït el problema a caracteritzar")
    print("només 8 taules M base.")

if __name__ == "__main__":
    main()
