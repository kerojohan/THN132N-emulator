#!/usr/bin/env python3
"""
Genera una LUT completa de P combinant TOTES les captures de tots els Nib7.
Utilitza les transformacions XOR descobertes per omplir buits.
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"
OUTPUT_DIR = Path(__file__).parent / "Docs"

# Transformacions XOR descobertes (base: Nib7=2)
NIB7_XOR_FROM_BASE = {
    0x0: 0x6,  # P(0) = P(2) XOR 0x6
    0x1: 0xD,  # P(1) = P(2) XOR 0xD
    0x2: 0x0,  # P(2) = P(2) (base)
    0x8: 0x7,  # P(8) = P(2) XOR 0x7
}

def extract_complete_lut():
    """Extreu i combina P de totes les captures."""
    
    # Estructura: lut[temp_idx][nib7] = p
    lut_by_temp_and_nib7 = defaultdict(dict)
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                if house != 247:  # Només House 247
                    continue
                
                temp_c = float(row['temperature_C'])
                payload_hex = row['payload64_hex']
                
                nibbles = [int(c, 16) for c in payload_hex]
                nib7 = nibbles[7]
                p = nibbles[14]
                
                temp_idx = int(round((temp_c + 40) * 10))
                
                # Guardar
                if nib7 not in lut_by_temp_and_nib7[temp_idx]:
                    lut_by_temp_and_nib7[temp_idx][nib7] = p
                    
            except (ValueError, KeyError):
                continue
    
    # Crear LUT final combinada
    # Estratègia: Per cada temperatura, usar el valor més comú o calcular via XOR
    final_lut = {}
    
    for temp_idx in sorted(lut_by_temp_and_nib7.keys()):
        nib7_values = lut_by_temp_and_nib7[temp_idx]
        
        # Si tenim Nib7=2 (base), usar-lo directament
        if 0x2 in nib7_values:
            final_lut[temp_idx] = nib7_values[0x2]
        # Sinó, intentar calcular des d'altres nib7 via XOR invers
        elif 0x1 in nib7_values:
            # P(2) = P(1) XOR 0xD
            final_lut[temp_idx] = nib7_values[0x1] ^ 0xD
        elif 0x0 in nib7_values:
            # P(2) = P(0) XOR 0x6
            final_lut[temp_idx] = nib7_values[0x0] ^ 0x6
        elif 0x8 in nib7_values:
            # P(2) = P(8) XOR 0x7
            final_lut[temp_idx] = nib7_values[0x8] ^ 0x7
    
    return final_lut

def generate_python_lut(lut, output_file):
    """Genera un fitxer Python amb la LUT."""
    
    with open(output_file, 'w') as f:
        f.write('"""\n')
        f.write('LUT Completa de P per Oregon Scientific THN132N (House 247)\n')
        f.write('Generada automàticament combinant totes les captures.\n')
        f.write('"""\n\n')
        
        f.write('# Transformacions XOR per diferents rolling codes\n')
        f.write('NIB7_XOR_TABLE = {\n')
        for nib7, xor_val in sorted(NIB7_XOR_FROM_BASE.items()):
            f.write(f'    0x{nib7:X}: 0x{xor_val:X},\n')
        f.write('}\n\n')
        
        f.write('# LUT Base (per Nib7=2)\n')
        f.write('# Índex: temp_idx = int((temp_c + 40) * 10)\n')
        f.write('P_LUT_BASE = {\n')
        
        for temp_idx in sorted(lut.keys()):
            temp_c = (temp_idx - 400) / 10
            p = lut[temp_idx]
            f.write(f'    {temp_idx:4d}: 0x{p:X},  # {temp_c:6.1f}°C\n')
        
        f.write('}\n\n')
        
        f.write('def get_p(temp_celsius, nib7=0x2):\n')
        f.write('    """\n')
        f.write('    Obté P per una temperatura i rolling code.\n')
        f.write('    \n')
        f.write('    Args:\n')
        f.write('        temp_celsius: Temperatura en °C\n')
        f.write('        nib7: Rolling code (0, 1, 2, o 8)\n')
        f.write('    \n')
        f.write('    Returns:\n')
        f.write('        Nibble P (0-F)\n')
        f.write('    """\n')
        f.write('    temp_idx = int(round((temp_celsius + 40) * 10))\n')
        f.write('    \n')
        f.write('    # Obtenir P base (Nib7=2)\n')
        f.write('    if temp_idx not in P_LUT_BASE:\n')
        f.write('        # Temperatura fora de rang - usar més proper\n')
        f.write('        closest_idx = min(P_LUT_BASE.keys(), key=lambda k: abs(k - temp_idx))\n')
        f.write('        p_base = P_LUT_BASE[closest_idx]\n')
        f.write('    else:\n')
        f.write('        p_base = P_LUT_BASE[temp_idx]\n')
        f.write('    \n')
        f.write('    # Aplicar transformació XOR\n')
        f.write('    xor_val = NIB7_XOR_TABLE.get(nib7, 0x0)\n')
        f.write('    return (p_base ^ xor_val) & 0xF\n')

def generate_statistics(lut):
    """Genera estadístiques de la LUT."""
    
    if not lut:
        return
    
    temp_indices = sorted(lut.keys())
    temp_min = (min(temp_indices) - 400) / 10
    temp_max = (max(temp_indices) - 400) / 10
    
    print(f"\\nEstadístiques de la LUT generada:")
    print(f"  Punts totals: {len(lut)}")
    print(f"  Rang temperatura: {temp_min:.1f}°C a {temp_max:.1f}°C")
    print(f"  Resolució: 0.1°C")
    print(f"  Mida memòria: ~{len(lut) * 2} bytes (1 byte per entrada)")
    
    # Distribució de valors P
    from collections import Counter
    p_dist = Counter(lut.values())
    print(f"\\n  Distribució valors P:")
    for p_val in sorted(p_dist.keys()):
        count = p_dist[p_val]
        print(f"    0x{p_val:X}: {count:3d} vegades ({count/len(lut)*100:5.1f}%)")

if __name__ == "__main__":
    print("Extraient LUT completa de P...")
    lut = extract_complete_lut()
    
    generate_statistics(lut)
    
    # Generar fitxer Python
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / "oregon_p_lut_complete.py"
    
    print(f"\\nGenerant fitxer: {output_file}")
    generate_python_lut(lut, output_file)
    
    print(f"\\n✅ LUT completa generada amb èxit!")
    print(f"   Ubicació: {output_file}")
