#!/usr/bin/env python3
"""
Intenta trobar l'algoritme per P (3r nibble del checksum).
Prova CRC-8 i sumes ponderades sobre els nibbles.
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CSV_FILE = BASE_DIR / "ec40_live.csv"

def get_nibbles(hex_str):
    return [int(c, 16) for c in hex_str]

def crc8(data, poly, init=0):
    crc = init
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
        crc &= 0xFF
    return crc

def crc4(data_nibbles, poly, init=0):
    crc = init
    for nibble in data_nibbles:
        crc ^= nibble
        for _ in range(4):
            if crc & 0x8:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
        crc &= 0xF
    return crc

def solve_p():
    data = []
    with open(CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = row['raw64']
            checksum_hex = row['checksum_hex']
            
            if not raw or not checksum_hex: continue
            
            try:
                # Raw: payload + checksum
                # Checksum són els últims 3 nibbles?
                # ec401da21810 243 a
                # Payload: ec401da21810 (12 nibbles)
                # Checksum: 243 (3 nibbles)
                # P és l'últim nibble del checksum (3)
                
                payload_str = raw[:12]
                payload_nibbles = get_nibbles(payload_str)
                
                # Target P is the last nibble of checksum_hex
                target_p = int(checksum_hex[-1], 16)
                
                data.append((payload_nibbles, target_p))
            except:
                continue
                
    print(f"Carregats {len(data)} registres.")
    
    # 1. Provar CRC-4 sobre nibbles
    print("\nProvant CRC-4...")
    for poly in range(16):
        for init in range(16):
            matches = 0
            for nibbles, target in data:
                if crc4(nibbles, poly, init) == target:
                    matches += 1
            
            if matches > len(data) * 0.9:
                print(f"  Posible CRC-4: Poly=0x{poly:X}, Init=0x{init:X} -> {matches}/{len(data)}")

    # 2. Provar CRC-8 sobre bytes (resultat & 0xF o >> 4)
    print("\nProvant CRC-8...")
    # Convertir nibbles a bytes
    byte_data = []
    for nibbles, target in data:
        bytes_val = []
        for i in range(0, len(nibbles), 2):
            b = (nibbles[i] << 4) | nibbles[i+1]
            bytes_val.append(b)
        byte_data.append((bytes_val, target))
        
    for poly in range(256):
        # Optimització: només algunes inits
        for init in [0, 0xFF, 0x55, 0xAA]:
            matches_lo = 0
            matches_hi = 0
            
            for bytes_val, target in byte_data:
                c = crc8(bytes_val, poly, init)
                if (c & 0xF) == target: matches_lo += 1
                if ((c >> 4) & 0xF) == target: matches_hi += 1
            
            if matches_lo > len(data) * 0.9:
                print(f"  Posible CRC-8 (Lo): Poly=0x{poly:X}, Init=0x{init:X} -> {matches_lo}/{len(data)}")
            if matches_hi > len(data) * 0.9:
                print(f"  Posible CRC-8 (Hi): Poly=0x{poly:X}, Init=0x{init:X} -> {matches_hi}/{len(data)}")

if __name__ == "__main__":
    solve_p()
