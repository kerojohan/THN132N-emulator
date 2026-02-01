#!/usr/bin/env python3
"""
Informe detallat de l'anàlisi de les taules M i P
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent


def load_data():
    """Carrega dades dels arxius CSV"""
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
            reader = csv.DictReader(f)
            all_data.extend(list(reader))
    
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


def generate_report():
    """Genera informe complet"""
    data = load_data()
    
    # Agrupar per house code
    by_house = defaultdict(list)
    for row in data:
        try:
            house = int(row['house_code'])
            by_house[house].append(row)
        except (ValueError, KeyError):
            continue
    
    print("# Informe d'anàlisi de taules M i P\n")
    print(f"**Total registres nets:** {len(data)}")
    print(f"**House codes únics:** {len(by_house)}\n")
    
    print("## Resum per House Code\n")
    print("| House | Mostres | Temp Min | Temp Max | Rang |")
    print("|-------|---------|----------|----------|------|")
    
    house_summary = []
    for house_code in sorted(by_house.keys()):
        temps = [float(r['temp']) for r in by_house[house_code] if 'temp' in r]
        if temps:
            min_temp = min(temps)
            max_temp = max(temps)
            rang = max_temp - min_temp
            house_summary.append((house_code, len(temps), min_temp, max_temp, rang))
            print(f"| {house_code:3d} | {len(temps):4d} | {min_temp:6.1f}°C | {max_temp:6.1f}°C | {rang:5.1f}°C |")
    
    print("\n## Troballes\n")
    
    print("### 1. Dades disponibles\n")
    print(f"- Tens dades de **{len(by_house)} house IDs diferents**")
    print(f"- El rang total de temperatura és de {min([h[2] for h in house_summary]):.1f}°C a {max([h[3] for h in house_summary]):.1f}°C")
    
    print("\n### 2. Problema de superposició\n")
    print("Per poder analitzar patrons XOR entre diferents house codes, necessitem:")
    print("- **Mateix rang de temperatures** per comparar els valors M i P")
    print("- **Prou mostres** en el rang compartit\n")
    
    # Analitzar superposició
    print("#### Anàlisi de superposició entre house codes:\n")
    
    overlaps = []
    house_codes = sorted(by_house.keys())
    for i, h1 in enumerate(house_codes):
        for h2 in house_codes[i+1:]:
            temps1 = set(int(float(r['temp'])*10) for r in by_house[h1] if 'temp' in r)
            temps2 = set(int(float(r['temp'])*10) for r in by_house[h2] if 'temp' in r)
            overlap = temps1 & temps2
            
            if len(overlap) > 5:  # Mínim 5 punts en comú
                overlaps.append((h1, h2, len(overlap)))
    
    if overlaps:
        overlaps.sort(key=lambda x: x[2], reverse=True)
        print("Parells amb bona superposició (>5 punts):\n")
        for h1, h2, count in overlaps[:10]:
            print(f"- House {h1} vs House {h2}: {count} punts de temperatura en comú")
    else:
        print("⚠️ **No hi ha parells de house codes amb suficient superposició de temperatures!**\n")
        print("Això significa que cada sensor s'ha capturat en diferents condicions ambientals.")
    
    print("\n### 3. Anàlisi de taula M\n")
    print("Basant-nos en estudis anteriors (House 3 vs House 96):")
    print("- La taula M segueix un patró XOR **condicional**")
    print("- Sembla dependre del house_code i possiblement de la temperatura\n")
    
    print("### 4. Anàlisi de taula P\n")
    print("Basant-nos en estudis anteriors (House 3 vs House 247):")
    print("- La taula P sembla seguir un patró XOR **constant**")
    print("- `P_house2 = P_house1 XOR (constant)`\n")
    
    print("## Propostes per continuar l'anàlisi\n")
    print("### Opció 1: Captlades dirigides")
    print("1. Triar 2-3 house IDs")
    print("2. Capturar dades de cadascun en el **mateix rang de temperatures** (ex: 15-30°C)")
    print("3. Analitzar els patrons XOR amb dades comparables\n")
    
    print("### Opció 2: Anàlisi teòrica")
    print("1. Estudiar el codi font del THN132N (si està disponible)")
    print("2. Analitzar com es generen les taules M i P internament")
    print("3. Implementar una funció que reprodueixi aquest càlcul\n")
    
    print("### Opció 3: Enginyeria inversa amb les dades existents")
    print("1. Utilitzar les parells amb millor superposició")
    print("2. Analitzar patrons dins de cada house code")
    print("3. Buscar relacions amb altres paràmetres (rolling_code, etc.)\n")


if __name__ == "__main__":
    generate_report()
