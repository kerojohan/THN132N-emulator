#!/usr/bin/env python3
"""
Genera un document de verificació detallat comparant captures vs generador.
"""

import csv
import sys
from pathlib import Path

# Afegir el path de Docs per importar la LUT
sys.path.insert(0, str(Path(__file__).parent / "Docs"))

from oregon_p_lut_complete import get_p

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"
OUTPUT_DIR = Path(__file__).parent / "Docs"

def generate_frame(house_id, channel, temp_celsius, rolling_code=0x2):
    """Genera trama completa de 15 nibbles."""
    nibbles = []
    
    # 1. ID (EC40)
    nibbles.extend([0xE, 0xC, 0x4, 0x0])
    
    # 2. Channel
    nibbles.append(channel & 0xF)
    
    # 3. House
    nibbles.append(house_id & 0xF)
    nibbles.append((house_id >> 4) & 0xF)
    
    # 4. Rolling code
    nibbles.append(rolling_code & 0xF)
    
    # 5. Temperatura BCD
    temp_abs = abs(temp_celsius)
    temp_int = int(round(temp_abs * 10))
    nibbles.append(temp_int % 10)
    nibbles.append((temp_int // 10) % 10)
    nibbles.append((temp_int // 100) % 10)
    
    # 6. Flags
    flags = 0x0 if temp_celsius >= 0 else 0x8
    nibbles.append(flags)
    
    # 7. R1, M (checksum senzill)
    total_sum = sum(nibbles)
    checksum_byte = total_sum & 0xFF
    r1 = checksum_byte & 0xF
    m = (checksum_byte >> 4) & 0xF
    nibbles.extend([r1, m])
    
    # 8. P (LUT + XOR transform)
    p = get_p(temp_celsius, rolling_code)
    nibbles.append(p)
    
    return nibbles

def create_verification_table():
    """Crea taula de verificació completa."""
    
    print("Carregant captures i generant trames...")
    
    results = []
    total = 0
    matches = 0
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                house = int(row['house'])
                channel = int(row['channel'])
                temp_c = float(row['temperature_C'])
                timestamp = row['timestamp']
                captured_hex = row['payload64_hex']
                
                # Nibbles capturats
                captured_nibbles = [int(c, 16) for c in captured_hex]
                nib7 = captured_nibbles[7]
                
                # Generar trama
                generated_nibbles = generate_frame(house, channel, temp_c, nib7)
                
                # Comparar (primers 15 nibbles)
                captured_15 = captured_nibbles[:15]
                match = (generated_nibbles == captured_15)
                
                total += 1
                if match:
                    matches += 1
                
                # Identificar diferències nibble a nibble
                diffs = []
                for i in range(15):
                    if captured_15[i] != generated_nibbles[i]:
                        diffs.append({
                            'pos': i,
                            'captured': captured_15[i],
                            'generated': generated_nibbles[i]
                        })
                
                results.append({
                    'timestamp': timestamp,
                    'house': house,
                    'channel': channel,
                    'temp': temp_c,
                    'nib7': nib7,
                    'captured': ''.join(f'{n:x}' for n in captured_15),
                    'generated': ''.join(f'{n:x}' for n in generated_nibbles),
                    'match': match,
                    'diffs': diffs
                })
                
            except (ValueError, KeyError) as e:
                continue
    
    print(f"\nProcessades {total} trames")
    print(f"Matches: {matches} ({matches/total*100:.2f}%)")
    print(f"Errors: {total-matches}")
    
    return results

def generate_markdown_table(results, output_file):
    """Genera taula en format Markdown."""
    
    with open(output_file, 'w') as f:
        f.write("# Taula de Verificació - Captures vs Generador\n\n")
        f.write(f"**Total trames**: {len(results)}\n")
        
        matches = sum(1 for r in results if r['match'])
        f.write(f"**Matches**: {matches} ({matches/len(results)*100:.2f}%)\n")
        f.write(f"**Errors**: {len(results)-matches}\n\n")
        
        # Estadístiques per House
        from collections import defaultdict, Counter
        
        by_house = defaultdict(list)
        for r in results:
            by_house[r['house']].append(r['match'])
        
        f.write("## Estadístiques per House\n\n")
        f.write("| House | Total | Matches | Errors | Precisió |\n")
        f.write("|-------|-------|---------|--------|----------|\n")
        
        for house in sorted(by_house.keys()):
            total_h = len(by_house[house])
            matches_h = sum(by_house[house])
            errors_h = total_h - matches_h
            pct = matches_h / total_h * 100
            
            status = "✅" if pct > 99 else "⚠️" if pct > 90 else "❌"
            f.write(f"| {house} | {total_h} | {matches_h} | {errors_h} | {pct:.1f}% {status} |\n")
        
        # Estadístiques per Nib7
        by_nib7 = defaultdict(list)
        for r in results:
            by_nib7[r['nib7']].append(r['match'])
        
        f.write("\n## Estadístiques per Rolling Code (Nib7)\n\n")
        f.write("| Nib7 | Total | Matches | Errors | Precisió |\n")
        f.write("|------|-------|---------|--------|----------|\n")
        
        for nib7 in sorted(by_nib7.keys()):
            total_n = len(by_nib7[nib7])
            matches_n = sum(by_nib7[nib7])
            errors_n = total_n - matches_n
            pct = matches_n / total_n * 100
            
            status = "✅" if pct > 99 else "⚠️" if pct > 90 else "❌"
            f.write(f"| 0x{nib7:X} | {total_n} | {matches_n} | {errors_n} | {pct:.1f}% {status} |\n")
        
        # Anàlisi d'errors
        errors_only = [r for r in results if not r['match']]
        
        if errors_only:
            f.write(f"\n## Anàlisi d'Errors ({len(errors_only)} total)\n\n")
            
            # Errors per posició
            error_positions = Counter()
            for r in errors_only:
                for diff in r['diffs']:
                    error_positions[diff['pos']] += 1
            
            f.write("### Errors per Posició de Nibble\n\n")
            f.write("| Posició | Descripció | Errors | % |\n")
            f.write("|---------|------------|--------|---|\n")
            
            position_names = {
                0: "ID (E)", 1: "ID (C)", 2: "ID (4)", 3: "ID (0)",
                4: "Channel", 5: "House LSN", 6: "House MSN",
                7: "Rolling Code", 8: "Temp LSN", 9: "Temp Mid",
                10: "Temp MSN", 11: "Flags", 12: "R1", 13: "M", 14: "P"
            }
            
            for pos in sorted(error_positions.keys()):
                count = error_positions[pos]
                pct = count / len(errors_only) * 100
                name = position_names.get(pos, f"Pos {pos}")
                f.write(f"| {pos} | {name} | {count} | {pct:.1f}% |\n")
            
            # Mostrar primers 10 errors
            f.write("\n### Primers 10 Errors Detallats\n\n")
            f.write("| # | House | Ch | Temp | Nib7 | Capturada | Generada | Diferències |\n")
            f.write("|---|-------|----|----|------|-----------|----------|-------------|\n")
            
            for i, r in enumerate(errors_only[:10], 1):
                diffs_str = ", ".join([f"pos{d['pos']}:{d['captured']:X}→{d['generated']:X}" for d in r['diffs']])
                f.write(f"| {i} | {r['house']} | {r['channel']} | {r['temp']:.1f}°C | 0x{r['nib7']:X} | `{r['captured']}` | `{r['generated']}` | {diffs_str} |\n")
        
        f.write("\n---\n\n")
        f.write("**Generador**: `oregon_optimized_generator.py` amb `oregon_p_lut_complete.py`\n")
        f.write(f"**Data**: {results[0]['timestamp'].split()[0]} - {results[-1]['timestamp'].split()[0]}\n")

def generate_csv_table(results, output_file):
    """Genera taula en format CSV."""
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Capçalera
        writer.writerow([
            'Timestamp', 'House', 'Channel', 'Temp_C', 'Nib7',
            'Captured', 'Generated', 'Match', 'Diffs'
        ])
        
        # Dades
        for r in results:
            diffs_str = ';'.join([f"{d['pos']}:{d['captured']:X}→{d['generated']:X}" for d in r['diffs']])
            
            writer.writerow([
                r['timestamp'],
                r['house'],
                r['channel'],
                f"{r['temp']:.1f}",
                f"0x{r['nib7']:X}",
                r['captured'],
                r['generated'],
                'OK' if r['match'] else 'ERROR',
                diffs_str if diffs_str else '-'
            ])

if __name__ == "__main__":
    # Crear taula de verificació
    results = create_verification_table()
    
    # Generar documents
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    md_file = OUTPUT_DIR / "verification_table.md"
    csv_file = OUTPUT_DIR / "verification_table.csv"
    
    print(f"\nGenerant documents...")
    generate_markdown_table(results, md_file)
    generate_csv_table(results, csv_file)
    
    print(f"\n✅ Documents generats:")
    print(f"   - {md_file}")
    print(f"   - {csv_file}")
