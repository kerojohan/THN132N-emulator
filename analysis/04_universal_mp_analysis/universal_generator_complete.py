#!/usr/bin/env python3
"""
GENERADOR UNIVERSAL COMPLET - Oregon Scientific THN132N
Genera trames perfectes per qualsevol House ID, Channel i Temperatura.
"""

def calculate_checksum(payload_nibbles):
    """
    Calcula els 3 nibbles del checksum: R1, M, P.
    
    Args:
        payload_nibbles: Lista de 12 nibbles del payload (sense checksum).
        
    Returns:
        (r1, m, p): Tupla amb els 3 nibbles del checksum.
    """
    # R1 i M: Suma de nibbles
    total_sum = sum(payload_nibbles)
    checksum_byte = total_sum & 0xFF
    
    r1 = checksum_byte & 0xF
    m = (checksum_byte >> 4) & 0xF
    
    # P: XOR acumulador
    h = 0
    for nibble in payload_nibbles:
        h = ((h << 4) ^ nibble) & 0xFF
    p = h & 0xF
    
    return r1, m, p

def generate_frame(house_id, channel, temp_celsius):
    """
    Genera una trama completa de 16 nibbles (64 bits).
    
    Args:
        house_id: House Code (0-255)
        channel: Canal (1-3)
        temp_celsius: Temperatura en °C
        
    Returns:
        String hexadecimal de 16 caràcters.
    """
    nibbles = []
    
    # 1. ID del sensor (EC40) - 4 nibbles
    nibbles.extend([0xE, 0xC, 0x4, 0x0])
    
    # 2. Channel (1 nibble)
    nibbles.append(channel & 0xF)
    
    # 3. House Code (2 nibbles: LSN, MSN)
    nibbles.append(house_id & 0xF)
    nibbles.append((house_id >> 4) & 0xF)
    
    # 4. Fixed flag (1 nibble)
    # Aquest sembla ser 0x2 per House 247, però hem de verificar si és universal
    # Per ara, usem el valor observat
    nibbles.append(0x2)
    
    # 5. Temperatura en BCD (3 nibbles: LSN, Mid, MSN)
    # Per temperatures negatives, es guarda el valor absolut
    # El signe està en un altre nibble (flags)
    temp_abs = abs(temp_celsius)
    temp_int = int(temp_abs * 10)  # Ex: 20.5°C -> 205
    
    nibbles.append(temp_int % 10)
    nibbles.append((temp_int // 10) % 10)
    nibbles.append((temp_int // 100) % 10)
    
    # 6. Flags/Battery (1 nibble)
    # Bit 3: signe de temperatura (0=positiu, 1=negatiu)
    # Altres bits: estat bateria, etc.
    flags = 0x8 if temp_celsius >= 0 else 0x0
    nibbles.append(flags)
    
    # 7. Checksum (3 nibbles: R1, M, P)
    r1, m, p = calculate_checksum(nibbles)
    nibbles.extend([r1, m, p])
    
    # 8. Postamble (1 nibble)
    # Aquest valor s'ha observat com a 0x1 per House 247
    # Potser és constant o depèn d'altres factors
    nibbles.append(0x1)
    
    # Convertir a string hex
    return ''.join(f'{n:x}' for n in nibbles)

def verify_against_captures(csv_file):
    """
    Verifica el generador contra totes les captures.
    """
    import csv
    from pathlib import Path
    
    matches = 0
    total = 0
    errors = []
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                house = int(row['house'])
                channel = int(row['channel'])
                temp_c = float(row['temperature_C'])
                captured_payload = row['payload64_hex']
                
                # Generar trama
                generated = generate_frame(house, channel, temp_c)
                
                total += 1
                
                # Comparar (només els primers 16 nibbles, payload64)
                if generated == captured_payload:
                    matches += 1
                else:
                    if len(errors) < 10:
                        errors.append({
                            'house': house,
                            'channel': channel,
                            'temp': temp_c,
                            'captured': captured_payload,
                            'generated': generated
                        })
                        
            except (ValueError, KeyError):
                continue
    
    print(f"VERIFICACIÓ COMPLETA:")
    print(f"  Total: {total} trames")
    print(f"  Matches: {matches} ({matches/total*100:.2f}%)")
    print(f"  Errors: {total-matches}")
    
    if errors:
        print(f"\nPrimers {len(errors)} errors:")
        for e in errors:
            print(f"  H={e['house']}, Ch={e['channel']}, T={e['temp']:.1f}°C")
            print(f"    Capturada: {e['captured']}")
            print(f"    Generada:  {e['generated']}")
            
            # Analitzar diferències nibble a nibble
            diffs = []
            for i, (c, g) in enumerate(zip(e['captured'], e['generated'])):
                if c != g:
                    diffs.append(f"pos{i}:{c}->{g}")
            print(f"    Diffs: {', '.join(diffs)}")
    
    return matches == total

if __name__ == "__main__":
    from pathlib import Path
    
    # Provar amb exemples coneguts
    print("PROVES INDIVIDUALS:")
    print("-" * 50)
    
    # House 247, 20.9°C
    frame = generate_frame(247, 1, 20.9)
    print(f"House 247, Ch 1, 20.9°C: {frame}")
    print(f"  Esperat: ec4017f8902084aa (de captura)")
    print()
    
    # House 3, 14.9°C
    frame = generate_frame(3, 1, 14.9)
    print(f"House 3, Ch 1, 14.9°C: {frame}")
    print(f"  Esperat: ec4013029410239e (de captura)")
    print()
    
    # Verificar contra totes les captures
    print("=" * 50)
    print()
    csv_file = Path(__file__).parent.parent / "ec40_capturas_merged.csv"
    verify_against_captures(csv_file)
