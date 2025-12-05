#!/usr/bin/env python3
"""
Solver P: Test específic de CRC-8 Poly 0x07 (Oregon v2.1).
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CSV_FILE = BASE_DIR / "ec40_live.csv"

def get_nibbles(hex_str):
    return [int(c, 16) for c in hex_str]

def crc8_oregon(nibbles, poly=0x07, init=0x00):
    """
    Implementació CRC-8 específica per Oregon Scientific.
    - Input: Llista de nibbles.
    - Processament: Nibble a nibble, o byte a byte?
    - Bit order: MSB first per al CRC (segons documentació).
    """
    crc = init
    
    # Processar per nibbles (com diu la doc: "send each nibble MSB first")
    for n in nibbles:
        # El nibble ja està en format 0..15 (0000..1111).
        # Si el CRC espera MSB first, i el nibble és 0xN, processem els 4 bits.
        
        # Shift in 4 bits
        for i in range(3, -1, -1):
            bit = (n >> i) & 1
            
            # CRC logic (MSB first)
            # Check if MSB of CRC is 1
            if (crc & 0x80):
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
            
            # Add new bit
            if bit:
                crc ^= 1 # XOR into LSB? No, standard CRC shifts in.
                # Standard CRC-8 shift:
                # crc ^= (bit << 7)? No.
                
    return crc & 0xFF

def crc8_standard(data_bytes, poly=0x07, init=0x00):
    crc = init
    for b in data_bytes:
        crc ^= b
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
        crc &= 0xFF
    return crc

def solve_targeted():
    data = []
    with open(CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = row['raw64']
            checksum_hex = row['checksum_hex']
            if not raw or not checksum_hex: continue
            try:
                # Payload: Tot menys els últims 3 nibbles (R1, M, P)
                # O tot menys l'últim (P)?
                # Si M/R1 són checksum aritmètic, potser el CRC es calcula sobre ells també?
                # O potser P és part del CRC i M/R1 no?
                
                # Provem diferents longituds de payload
                full_nibbles = get_nibbles(raw)
                target_p = int(checksum_hex[-1], 16)
                
                data.append({
                    'full': full_nibbles,
                    'target': target_p
                })
            except:
                continue

    print(f"Provant CRC-8 Poly 0x07 amb {len(data)} mostres...")
    
    # Provem diferents rangs de dades d'entrada
    # 1. Payload sense Checksum (0..-3)
    # 2. Payload + M/R1 (0..-1)
    ranges = [
        ('PayloadOnly', lambda x: x[:-3]),
        ('Payload+CS', lambda x: x[:-1]),
        ('Payload+CS_Swapped', lambda x: x[:-3] + [x[-2], x[-1]]) # R1, M order?
    ]
    
    for name, slicer in ranges:
        print(f"\nRang: {name}")
        
        # Brute force Init value
        for init in range(256):
            matches = 0
            for d in data:
                nibbles = slicer(d['full'])
                
                # Convert to bytes for standard CRC
                bytes_val = []
                for i in range(0, len(nibbles), 2):
                    if i+1 < len(nibbles):
                        b = (nibbles[i] << 4) | nibbles[i+1]
                        bytes_val.append(b)
                
                # Calc CRC
                c = crc8_standard(bytes_val, poly=0x07, init=init)
                
                # Check if P matches any part of CRC
                if (c & 0xF) == d['target']: matches += 1
                elif ((c >> 4) & 0xF) == d['target']: matches += 1
                
            if matches > len(data) * 0.9:
                print(f"  ✨ POSSIBLE CRC-8! Init=0x{init:X} -> {matches}/{len(data)}")

if __name__ == "__main__":
    solve_targeted()
