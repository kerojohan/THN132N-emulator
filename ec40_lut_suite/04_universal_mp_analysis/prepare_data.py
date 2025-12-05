#!/usr/bin/env python3
"""
Prepara el dataset 'Golden Master' per a l'anàlisi de força bruta.
Llegeix els CSVs, filtra outliers, i guarda en format optimitzat.
"""

import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
OUTPUT_FILE = BASE_DIR / "04_universal_mp_analysis" / "golden_master.csv"

def load_and_clean_data():
    CSV_FILES = [
        BASE_DIR / "ec40_live.csv",
        BASE_DIR / "ec40_live_1.csv", 
        BASE_DIR / "ec40_capturas_merged.csv"
    ]
    
    # Utilitzem un diccionari per filtrar duplicats i conflictes
    # Key: (house, temp_idx) -> Value: list of (m, p)
    data_map = defaultdict(list)
    
    for csv_file in CSV_FILES:
        if not csv_file.exists():
            continue
            
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    house = int(row['house_code'])
                    temp = float(row['temp'])
                    
                    # Convertir temp a index (0.1ºC resolució, offset -40)
                    # idx = (temp + 40) * 10
                    # Arrodonim per evitar errors de float
                    temp_idx = int(round((temp + 40) * 10))
                    
                    checksum_str = row.get('checksum_hex', row.get('R12', ''))
                    r12 = int(checksum_str, 16) if isinstance(checksum_str, str) else int(checksum_str)
                    m = (r12 >> 4) & 0xF
                    p = r12 & 0xF
                    
                    data_map[(house, temp_idx)].append((m, p))
                    
                except (ValueError, KeyError, TypeError):
                    continue
    
    # Processar conflictes
    clean_data = []
    conflicts = 0
    
    for (house, temp_idx), values in data_map.items():
        # Comprovar si tots els valors són iguals
        unique_values = set(values)
        
        if len(unique_values) == 1:
            m, p = list(unique_values)[0]
            clean_data.append({
                'house': house,
                'temp_idx': temp_idx,
                'temp_c': (temp_idx / 10.0) - 40.0,
                'm': m,
                'p': p
            })
        else:
            # Conflicte! (mateix house/temp, diferent M/P)
            # Això sol passar amb l'oscil·lació 3/4 en M
            # O soroll en P
            # Per ara, els descartem per no contaminar l'anàlisi
            conflicts += 1
            # Opcional: Podríem agafar el valor més freqüent
            
    print(f"Processats {len(data_map)} punts únics (House+Temp).")
    print(f"Descartats {conflicts} punts per conflictes/inconsistència.")
    print(f"Dataset final: {len(clean_data)} registres.")
    
    return clean_data

def save_golden_master(data):
    if not data:
        print("No hi ha dades per guardar!")
        return
        
    fieldnames = ['house', 'temp_idx', 'temp_c', 'm', 'p']
    
    # Assegurar directori
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        
    print(f"Guardat a: {OUTPUT_FILE}")

if __name__ == "__main__":
    data = load_and_clean_data()
    save_golden_master(data)
