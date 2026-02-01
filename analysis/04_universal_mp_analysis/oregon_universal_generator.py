#!/usr/bin/env python3
"""
GENERADOR UNIVERSAL FINAL - Oregon Scientific THN132N
Genera els primers 15 nibbles correctes (sense postamble).
"""

def calculate_checksum(payload_nibbles):
    """
    Calcula els 3 nibbles del checksum: R1, M, P.
    
    Args:
        payload_nibbles: Lista de 12 nibbles del payload (sense checksum).
        
    Returns:
        (r1, m, p): Tupla amb els 3 nibbles del checksum.
    """
    # R1 i M: Suma dels primers 12 nibbles
    total_sum = sum(payload_nibbles)
    checksum_byte = total_sum & 0xFF
    
    r1 = checksum_byte & 0xF
    m = (checksum_byte >> 4) & 0xF
    
    # P: XOR acumulador sobre primers 14 nibbles
    nibbles_14 = payload_nibbles + [r1, m]
    
    h = 0
    for nibble in nibbles_14:
        h = ((h << 4) ^ nibble) & 0xFF
    
    p = h & 0xF
    
    return r1, m, p

def generate_frame(house_id, channel, temp_celsius):
    """
    Genera els primers 15 nibbles d'una trama Oregon THN132N.
    
    Args:
        house_id: House Code (0-255)
        channel: Canal (1-3)
        temp_celsius: Temperatura en °C
        
    Returns:
        String hexadecimal de 15 caràcters (sense postamble).
    """
    nibbles = []
    
    # 1. ID del sensor (EC40) - 4 nibbles
    nibbles.extend([0xE, 0xC, 0x4, 0x0])
    
    # 2. Channel (1 nibble)
    nibbles.append(channel & 0xF)
    
    # 3. House Code (2 nibbles: LSN, MSN)
    nibbles.append(house_id & 0xF)
    nibbles.append((house_id >> 4) & 0xF)
    
    # 4. Fixed nibble (1 nibble) - Sempre 0x2
    nibbles.append(0x2)
    
    # 5. Temperatura en BCD (3 nibbles: LSN, Mid, MSN)
    temp_abs = abs(temp_celsius)
    temp_int = int(round(temp_abs * 10))  # Ex: 20.5°C -> 205
    
    nibbles.append(temp_int % 10)
    nibbles.append((temp_int // 10) % 10)
    nibbles.append((temp_int // 100) % 10)
    
    # 6. Flags (1 nibble)
    # Bit 3 = 0 per temp positiva, bit 3 = 1 per temp negativa
    # Invertit: 0x0 per positiu, 0x8 per negatiu
    flags = 0x0 if temp_celsius >= 0 else 0x8
    nibbles.append(flags)
    
    # 7. Checksum (3 nibbles: R1, M, P)
    r1, m, p = calculate_checksum(nibbles)
    nibbles.extend([r1, m, p])
    
    # Convertir a string hex (15 nibbles)
    return ''.join(f'{n:x}' for n in nibbles)

def verify_against_captures(csv_file):
    """
    Verifica el generador contra totes les captures (primers 15 nibbles).
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
                
                # Generar trama (15 nibbles)
                generated = generate_frame(house, channel, temp_c)
                
                # Comparar només els primers 15 nibbles
                captured_15 = captured_payload[:15]
                
                total += 1
                
                if generated == captured_15:
                    matches += 1
                else:
                    if len(errors) < 10:
                        errors.append({
                            'house': house,
                            'channel': channel,
                            'temp': temp_c,
                            'captured': captured_15,
                            'generated': generated
                        })
                        
            except (ValueError, KeyError):
                continue
    
    print(f"VERIFICACIÓ COMPLETA (15 nibbles):")
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
    else:
        print("\n✅ GENERADOR PERFECTE! Tots els primers 15 nibbles coincideixen.")
    
    return matches == total

if __name__ == "__main__":
    from pathlib import Path
    
    # Provar amb exemples coneguts
    print("PROVES INDIVIDUALS:")
    print("-" * 50)
    
    # House 247, 20.9°C
    frame = generate_frame(247, 1, 20.9)
    print(f"House 247, Ch 1, 20.9°C: {frame}")
    print(f"  Esperat (15 nibbles): ec4017f8902084a")
    print()
    
    # House 3, 14.9°C
    frame = generate_frame(3, 1, 14.9)
    print(f"House 3, Ch 1, 14.9°C: {frame}")
    print(f"  Esperat (15 nibbles): ec401302941023")
    print()
    
    # House 247, -15.0°C (negatiu)
    frame = generate_frame(247, 1, -15.0)
    print(f"House 247, Ch 1, -15.0°C: {frame}")
    print()
    
    # Verificar contra totes les captures
    print("=" * 50)
    print()
    csv_file = Path(__file__).parent.parent / "ec40_capturas_merged.csv"
    success = verify_against_captures(csv_file)
    
    if success:
        print("\n🎉 ÈXIT TOTAL! El generador és 100% precís.")
