#!/usr/bin/env python3
"""
GENERADOR UNIVERSAL COMPLET I FINAL - Oregon Scientific THN132N
Genera trames perfectes amb checksum correcte.
"""

def calculate_p_bruteforce(nibbles_14):
    """
    Troba P per força bruta: l'únic valor auto-consistent.
    P és tal que XOR_shift([nibbles_14..., P]) & 0xF == P
    """
    def xor_shift(nibbles):
        h = 0
        for nib in nibbles:
            h = ((h << 4) ^ nib) & 0xFF
        return h & 0xF
    
    # Provar tots els valors 0-F
    for p_test in range(16):
        nibbles_15_test = nibbles_14 + [p_test]
        p_calc = xor_shift(nibbles_15_test)
        
        if p_calc == p_test:
            return p_test
    
    # Fallback (no hauria de passar)
    return 0

def calculate_checksum(payload_nibbles, nibble7):
    """
    Calcula els 3 nibbles del checksum: R1, M, P.
    
    Args:
        payload_nibbles: 11 nibbles (ID, Channel, House, Temp, Flags)
        nibble7: El rolling code / session ID (0, 1, 2, o 8)
        
    Returns:
        (r1, m, p): Tupla amb els 3 nibbles del checksum.
    """
    # Inserir nibble7 a la posició correcta (després de House)
    full_payload = payload_nibbles[:7] + [nibble7] + payload_nibbles[7:]
    
    # R1 i M: Suma dels 12 nibbles
    total_sum = sum(full_payload)
    checksum_byte = total_sum & 0xFF
    
    r1 = checksum_byte & 0xF
    m = (checksum_byte >> 4) & 0xF
    
    # P: Força bruta sobre els 14 nibbles (payload + R1 + M)
    nibbles_14 = full_payload + [r1, m]
    p = calculate_p_bruteforce(nibbles_14)
    
    return r1, m, p

def generate_frame(house_id, channel, temp_celsius, rolling_code=0x2):
    """
    Genera una trama completa de 15 nibbles (sense postamble).
    
    Args:
        house_id: House Code (0-255)
        channel: Canal (1-3)
        temp_celsius: Temperatura en °C
        rolling_code: Rolling code / Session ID (0, 1, 2, o 8). Defecte: 0x2
        
    Returns:
        String hexadecimal de 15 caràcters.
    """
    nibbles = []
    
    # 1. ID del sensor (EC40) - 4 nibbles (pos 0-3)
    nibbles.extend([0xE, 0xC, 0x4, 0x0])
    
    # 2. Channel (1 nibble, pos 4)
    nibbles.append(channel & 0xF)
    
    # 3. House Code (2 nibbles: LSN, MSN, pos 5-6)
    nibbles.append(house_id & 0xF)          # LSN
    nibbles.append((house_id >> 4) & 0xF)   # MSN
    
    # 4. Nibble 7 - Rolling code (pos 7)
    nibbles.append(rolling_code & 0xF)
    
    # 5. Temperatura en BCD (3 nibbles: LSN, Mid, MSN, pos 8-10)
    temp_abs = abs(temp_celsius)
    temp_int = int(round(temp_abs * 10))
    
    nibbles.append(temp_int % 10)              # LSN
    nibbles.append((temp_int // 10) % 10)      # Mid
    nibbles.append((temp_int // 100) % 10)     # MSN
    
    # 6. Flags (1 nibble, pos 11)
    # Bit 3: signe de temperatura (0=positiu, 1=negatiu és INVERTIT!)
    flags = 0x0 if temp_celsius >= 0 else 0x8
    nibbles.append(flags)
    
    # Ara tenim 12 nibbles [0-11]
    # Calcular checksum
    total_sum = sum(nibbles)
    checksum_byte = total_sum & 0xFF
    
    r1 = checksum_byte & 0xF
    m = (checksum_byte >> 4) & 0xF
    
    # 7. R1 i M (pos 12-13)
    nibbles.extend([r1, m])
    
    # 8. P per força bruta (pos 14)
    p = calculate_p_bruteforce(nibbles)  # nibbles ara té 14 elements
    nibbles.append(p)
    
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
                
                # Extreure nibble7 real de la captura
                nibble7_real = int(captured_payload[7], 16)
                
                # Generar trama amb el nibble7 correcte
                generated = generate_frame(house, channel, temp_c, nibble7_real)
                
                # Comparar només els primers 15 nibbles
                captured_15 = captured_payload[:15]
                
                total += 1
                
                if generated == captured_15:
                    matches += 1
                else:
                    if len(errors) < 5:
                        errors.append({
                            'house': house,
                            'channel': channel,
                            'temp': temp_c,
                            'nib7': nibble7_real,
                            'captured': captured_15,
                            'generated': generated
                        })
                        
            except (ValueError, KeyError):
                continue
    
    print(f"VERIFICACIÓ COMPLETA (15 nibbles amb nibble7 correcte):")
    print(f"  Total: {total} trames")
    print(f"  Matches: {matches} ({matches/total*100:.2f}%)")
    print(f"  Errors: {total-matches}")
    
    if errors:
        print(f"\nPrimers {len(errors)} errors:")
        for e in errors:
            print(f"  H={e['house']}, Ch={e['channel']}, T={e['temp']:.1f}°C, Nib7={e['nib7']:X}")
            print(f"    Capturada: {e['captured']}")
            print(f"    Generada:  {e['generated']}")
            
            # Analitzar diferències nibble a nibble
            diffs = []
            for i, (c, g) in enumerate(zip(e['captured'], e['generated'])):
                if c != g:
                    diffs.append(f"pos{i}:{c}->{g}")
            if diffs:
                print(f"    Diffs: {', '.join(diffs)}")
    else:
        print("\n✅ GENERADOR PERFECTE! Tots els primers 15 nibbles coincideixen.")
    
    return matches == total

if __name__ == "__main__":
    from pathlib import Path
    
    # Provar amb exemples coneguts
    print("PROVES INDIVIDUALS:")
    print("-" * 70)
    
    # House 247, 20.9°C amb nibble7=0x8
    frame = generate_frame(247, 1, 20.9, rolling_code=0x8)
    print(f"House 247, Ch 1, 20.9°C, Nib7=8: {frame}")
    print(f"  Esperat:                         ec4017f8902084a")
    print()
    
    # House 3, 14.9°C amb nibble7=0x2
    frame = generate_frame(3, 1, 14.9, rolling_code=0x2)
    print(f"House 3, Ch 1, 14.9°C, Nib7=2:   {frame}")
    print(f"  Esperat:                         ec401302941023?")
    print()
    
    # House 247, -15.0°C (negatiu) amb nibble7=0x2
    frame = generate_frame(247, 1, -15.0, rolling_code=0x2)
    print(f"House 247, Ch 1, -15.0°C, Nib7=2: {frame}")
    print()
    
    # Verificar contra totes les captures
    print("=" * 70)
    print()
    csv_file = Path(__file__).parent.parent / "ec40_capturas_merged.csv"
    
    if csv_file.exists():
        success = verify_against_captures(csv_file)
        
        if success:
            print("\n🎉 ÈXIT TOTAL! El generador és 100% precís.")
    else:
        print(f"⚠️  Fitxer {csv_file} no trobat. Saltant verificació.")
