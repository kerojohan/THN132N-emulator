#!/usr/bin/env python3
"""
Analitza totes les captures per trobar com es generen les taules M i P
per qualsevol house ID. Versió sense pandas.
"""

import csv
from pathlib import Path
from collections import defaultdict

# Rutes dels arxius
BASE_DIR = Path(__file__).parent.parent
CSV_FILES = [
    BASE_DIR / "ec40_live.csv",
    BASE_DIR / "ec40_live_1.csv", 
    BASE_DIR / "ec40_capturas_merged.csv"
]

def load_and_merge_data():
    """Carrega i fusiona tots els arxius CSV"""
    all_data = []
    
    for csv_file in CSV_FILES:
        if not csv_file.exists():
            continue
            
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)
            all_data.extend(data)
            print(f"Carregat {csv_file.name}: {len(data)} registres")
    
    print(f"\nTotal registres: {len(all_data)}")
    return all_data

def filter_outliers(data):
    """
    Elimina registres amb mateix house_code, channel i temp
    però amb trames diferents (probablement errors)
    """
    # Agrupar per (house_code, channel, temp)
    groups = defaultdict(list)
    
    for row in data:
        try:
            key = (int(row['house_code']), int(row['channel']), float(row['temp']))
            groups[key].append(row)
        except (ValueError, KeyError):
            continue
    
    # Comptar duplicats
    duplicates_count = 0
    for key, rows in groups.items():
        frames = set(r.get('raw64', r.get('payload64_hex', '')) for r in rows)
        if len(frames) > 1:
            duplicates_count += len(rows) - 1
            house, channel, temp = key
            print(f"  House {house}, Ch{channel}, {temp:.1f}°C: {len(frames)} trames diferents")
    
    print(f"\nTrobats ~{duplicates_count} registres duplicats")
    
    # Mantenir només la primera ocurrència
    seen = set()
    clean_data = []
    
    for row in data:
        try:
            key = (int(row['house_code']), int(row['channel']), 
                   float(row['temp']), row.get('raw64', row.get('payload64_hex', '')))
            if key not in seen:
                seen.add(key)
                clean_data.append(row)
        except (ValueError, KeyError):
            continue
    
    print(f"Després de filtrar: {len(clean_data)} registres\n")
    return clean_data

def extract_m_p_values(row):
    """Extreu valors M i P del checksum R12"""
    checksum_str = row.get('checksum_hex', row.get('R12', ''))
    
    try:
        if isinstance(checksum_str, str):
            r12_int = int(checksum_str, 16) if checksum_str.startswith('0x') else int(checksum_str, 16)
        else:
            r12_int = int(checksum_str)
        
        m = (r12_int >> 4) & 0xF
        p = r12_int & 0xF
        
        return m, p, r12_int
    except (ValueError, AttributeError):
        return None, None, None

def build_mp_tables(data):
    """Construeix taules M i P per cada house_code"""
    mp_tables = {}
    
    # Agrupar per house_code
    by_house = defaultdict(list)
    for row in data:
        try:
            house = int(row['house_code'])
            by_house[house].append(row)
        except (ValueError, KeyError):
            continue
    
    for house_code in sorted(by_house.keys()):
        house_data = by_house[house_code]
        
        # Construir taules M i P
        m_table = [-1] * 256  # -1 = no definit
        p_table = [-1] * 256
        
        temp_min = temp_max = None
        
        for row in house_data:
            try:
                temp_c = float(row['temp'])
                
                if temp_min is None or temp_c < temp_min:
                    temp_min = temp_c
                if temp_max is None or temp_c > temp_max:
                    temp_max = temp_c
                
                m, p, _ = extract_m_p_values(row)
                
                if m is not None and p is not None:
                    if -40 <= temp_c <= 70:
                        idx = int((temp_c + 40) * 10)
                        if 0 <= idx < 256:
                            m_table[idx] = m
                            p_table[idx] = p
            except (ValueError, KeyError):
                continue
        
        mp_tables[house_code] = {
            'M_table': m_table,
            'P_table': p_table,
            'samples': len(house_data),
            'temp_range': (temp_min, temp_max) if temp_min is not None else (None, None)
        }
        
        if temp_min is not None:
            print(f"House {house_code:3d}: {len(house_data):4d} mostres, "
                  f"rang {temp_min:5.1f}°C a {temp_max:5.1f}°C")
    
    return mp_tables

def analyze_xor_patterns(mp_tables):
    """Analitza patrons XOR entre diferents house codes"""
    house_codes = sorted(mp_tables.keys())
    
    print(f"\n=== Anàlisi de patrons XOR entre {len(house_codes)} house codes ===\n")
    
    # Comparar cada parell de house codes
    comparisons = 0
    max_comparisons = 30
    
    for i, house1 in enumerate(house_codes):
        if comparisons >= max_comparisons:
            print(f"... (limitant a {max_comparisons} comparacions)\n")
            break
            
        for house2 in house_codes[i+1:]:
            if comparisons >= max_comparisons:
                break
                
            m1 = mp_tables[house1]['M_table']
            m2 = mp_tables[house2]['M_table']
            p1 = mp_tables[house1]['P_table']
            p2 = mp_tables[house2]['P_table']
            
            # Trobar índexs vàlids (on ambdós tenen dades)
            m_xor_values = []
            p_xor_values = []
            
            overlap_indices = []
            for idx in range(256):
                if m1[idx] != -1 and m2[idx] != -1:
                    m_xor_values.append(m1[idx] ^ m2[idx])
                    overlap_indices.append(idx)
                if p1[idx] != -1 and p2[idx] != -1:
                    p_xor_values.append(p1[idx] ^ p2[idx])
            
            if not m_xor_values or not p_xor_values:
                # print(f"House {house1:3d} vs House {house2:3d}: sense superposició")
                continue
            
            m_xor_unique = sorted(set(m_xor_values))
            p_xor_unique = sorted(set(p_xor_values))
            
            house_xor = house1 ^ house2
            
            print(f"House {house1:3d} (0x{house1:02X}) vs House {house2:3d} (0x{house2:02X})  [House XOR = 0x{house_xor:02X}]:")
            print(f"  Overlap: {len(m_xor_values)} punts de temperatura")
            print(f"  M: {len(m_xor_unique)} valors XOR únics: {[f'0x{v:X}' for v in m_xor_unique[:10]]}")
            print(f"  P: {len(p_xor_unique)} valors XOR únics: {[f'0x{v:X}' for v in p_xor_unique[:10]]}")
            
            # Si el XOR és constant, és una transformació simple
            if len(m_xor_unique) == 1:
                print(f"  ✓ M: XOR CONSTANT = 0x{m_xor_unique[0]:X}")
                # Comparar amb House XOR
                if m_xor_unique[0] == house_xor:
                    print(f"    💡 M_XOR == HOUSE_XOR (transformació directa!)")
                elif m_xor_unique[0] == (house_xor & 0xF):
                    print(f"    💡 M_XOR == HOUSE_XOR & 0xF")
            
            if len(p_xor_unique) == 1:
                print(f"  ✓ P: XOR CONSTANT = 0x{p_xor_unique[0]:X}")
            
            # Mostrar alguns exemples de valors
            if len(overlap_indices) > 0:
                sample_idx = overlap_indices[len(overlap_indices)//2]
                temp = (sample_idx / 10.0) - 40
                print(f"  Exemple (idx={sample_idx}, ~{temp:.1f}°C): M1={m1[sample_idx]}, M2={m2[sample_idx]}, XOR={m1[sample_idx]^m2[sample_idx]:X}")
            
            print()
            comparisons += 1

def main():
    print("=== Anàlisi de generació de taules M i P ===\n")
    
    # 1. Carregar dades
    data = load_and_merge_data()
    
    # 2. Filtrar outliers
    data_clean = filter_outliers(data)
    
    # 3. Construir taules M/P per cada house
    print("=== Taules M/P per House Code ===\n")
    mp_tables = build_mp_tables(data_clean)
    
    # 4. Analitzar patrons XOR
    analyze_xor_patterns(mp_tables)

if __name__ == "__main__":
    main()
