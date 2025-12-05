#!/usr/bin/env python3
"""
Analitza patrons XOR entre parells de house codes amb bona superposició
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent


def load_and_prepare_data():
    """Carrega i prepara dades"""
    CSV_FILES = [
        BASE_DIR / "ec40_live.csv",
        BASE_DIR / "ec40_live_1.csv", 
        BASE_DIR / "ec40_capturas_merged.csv"
    ]
    
    all_data = []
    for csv_file in CSV_FILES:
        if not csv_file.exists():
            continue
        with open(csv_file, 'r') as f:
            all_data.extend(list(csv.DictReader(f)))
    
    # Filtrar duplicats
    seen = set()
    clean_data = []
    for row in all_data:
        try:
            key = (int(row['house_code']), int(row['channel']), 
                   float(row['temp']), row.get('raw64', row.get('payload64_hex', '')))
            if key not in seen:
                seen.add(key)
                clean_data.append(row)
        except (ValueError, KeyError):
            continue
    
    return clean_data


def extract_m_p(row):
    """Extreu M i P"""
    checksum_str = row.get('checksum_hex', row.get('R12', ''))
    try:
        r12 = int(checksum_str, 16) if isinstance(checksum_str, str) else int(checksum_str)
        return (r12 >> 4) & 0xF, r12 & 0xF
    except:
        return None, None


def analyze_pair(data, house1, house2):
    """Analitza un parell de house codes amb superposició"""
    
    # Filtrar dades per cada house
    h1_data = {float(r['temp']): r for r in data if int(r.get('house_code', -1)) == house1}
    h2_data = {float(r['temp']): r for r in data if int(r.get('house_code', -1)) == house2}
    
    # Trobar temperatures comunes
    common_temps = sorted(set(h1_data.keys()) & set(h2_data.keys()))
    
    if len(common_temps) < 5:
        return None
    
    print(f"\n{'='*70}")
    print(f"House {house1} (0x{house1:02X}) vs House {house2} (0x{house2:02X})")
    print(f"House XOR: 0x{house1^house2:02X} = {house1^house2}")
    print(f"Temperatures comunes: {len(common_temps)}")
    print(f"Rang: {common_temps[0]:.1f}°C a {common_temps[-1]:.1f}°C")
    print(f"{'='*70}\n")
    
    # Analitzar valors M i P
    m_xors = []
    p_xors = []
    
    print("Temp    | M1  M2  M_XOR | P1  P2  P_XOR")
    print("--------|---------------|---------------")
    
    for temp in common_temps[:15]:  # Mostrar primers 15
        m1, p1 = extract_m_p(h1_data[temp])
        m2, p2 = extract_m_p(h2_data[temp])
        
        if m1 is not None and m2 is not None:
            m_xor = m1 ^ m2
            p_xor = p1 ^ p2
            m_xors.append(m_xor)
            p_xors.append(p_xor)
            
            print(f"{temp:6.1f}°C| {m1:2d}  {m2:2d}  0x{m_xor:X}   | {p1:2d}  {p2:2d}  0x{p_xor:X}")
    
    if len(common_temps) > 15:
        print(f"... ({len(common_temps)-15} temperatures més)")
    
    # Analitzar patrons
    m_unique = sorted(set(m_xors))
    p_unique = sorted(set(p_xors))
    
    print(f"\n📊 Anàlisi:")
    print(f"  M XOR: {len(m_unique)} valors únics: {m_unique}")
    print(f"  P XOR: {len(p_unique)} valors únics: {p_unique}")
    
    if len(m_unique) == 1:
        print(f"\n  ✅ Taula M: XOR CONSTANT = 0x{m_unique[0]:X}")
        if m_unique[0] == (house1 ^ house2):
            print(f"     💡 M_XOR == HOUSE_XOR (relació directa!)")
    else:
        print(f"\n  ⚠️  Taula M: XOR variable ({len(m_unique)} valors diferents)")
    
    if len(p_unique) == 1:
        print(f"\n  ✅ Taula P: XOR CONSTANT = 0x{p_unique[0]:X}")
    else:
        print(f"\n  ⚠️  Taula P: XOR variable ({len(p_unique)} valors diferents)")
    
    return {
        'overlap': len(common_temps),
        'm_xor_unique': m_unique,
        'p_xor_unique': p_unique
    }


def main():
    print("Anàlisi detallada de парells amb bona superposició\n")
    
    data = load_and_prepare_data()
    
    # Parells amb millor superposició (del report anterior)
    best_pairs = [
        (95, 121),
        (121, 124),
        (95, 124),
        (95, 187),
        (121, 187),
        (121, 232),
        (95, 232),
        (124, 131),
        (124, 184),
    ]
    
    results = []
    for h1, h2 in best_pairs:
        result = analyze_pair(data, h1, h2)
        if result:
            results.append((h1, h2, result))
    
    # Resum final
    print(f"\n\n{'='*70}")
    print("RESUM FINAL")
    print(f"{'='*70}\n")
    
    constant_m = []
    constant_p = []
    
    for h1, h2, res in results:
        if len(res['m_xor_unique']) == 1:
            constant_m.append((h1, h2, res['m_xor_unique'][0]))
        if len(res['p_xor_unique']) == 1:
            constant_p.append((h1, h2, res['p_xor_unique'][0]))
    
    print(f"Parells amb M XOR constant: {len(constant_m)}/{len(results)}")
    for h1, h2, xor_val in constant_m:
        print(f"  - House {h1} vs {h2}: M_XOR = 0x{xor_val:X}, House_XOR = 0x{h1^h2:02X}")
    
    print(f"\nParells amb P XOR constant: {len(constant_p)}/{len(results)}")
    for h1, h2, xor_val in constant_p:
        print(f"  - House {h1} vs {h2}: P_XOR = 0x{xor_val:X}")


if __name__ == "__main__":
    main()
