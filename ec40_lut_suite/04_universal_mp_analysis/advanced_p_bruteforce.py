#!/usr/bin/env python3
"""
Força bruta AVANÇADA: CRC, hashes, i algoritmes criptogràfics.
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def load_data():
    data = []
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                payload_hex = row['payload64_hex']
                nibbles = [int(c, 16) for c in payload_hex]
                
                data.append({
                    'nibbles_14': nibbles[:14],
                    'p': nibbles[14]
                })
            except (ValueError, KeyError):
                continue
    return data

def crc4_nibbles(nibbles, poly, init=0):
    """CRC-4 sobre nibbles."""
    crc = init
    for nib in nibbles:
        crc ^= nib
        for _ in range(4):
            if crc & 0x8:
                crc = ((crc << 1) ^ poly) & 0xF
            else:
                crc = (crc << 1) & 0xF
    return crc

def test_advanced_algorithms():
    data = load_data()
    print(f"Dataset: {len(data)} mostres\n")
    print("Provant CRC-4 amb tots els polinomis...\n")
    
    # Provar tots els polinomis CRC-4
    best_poly = None
    best_matches = 0
    
    for poly in range(16):
        for init in [0, 0xF]:
            matches = sum(1 for d in data if crc4_nibbles(d['nibbles_14'], poly, init) == d['p'])
            
            if matches > best_matches:
                best_matches = matches
                best_poly = (poly, init)
            
            if matches / len(data) > 0.9:
                print(f"✨ TROBAT! CRC-4 Poly=0x{poly:X}, Init=0x{init:X}: {matches}/{len(data)} ({matches/len(data)*100:.1f}%)")
                return
    
    poly, init = best_poly
    print(f"Millor CRC-4: Poly=0x{poly:X}, Init=0x{init:X}: {best_matches}/{len(data)} ({best_matches/len(data)*100:.1f}%)\n")
    
    # Provar Fletcher checksum (variant)
    print("Provant Fletcher-like checksums...")
    
    def fletcher_mod16(nibbles):
        sum1 = 0
        sum2 = 0
        for nib in nibbles:
            sum1 = (sum1 + nib) & 0xF
            sum2 = (sum2 + sum1) & 0xF
        return (sum1 ^ sum2) & 0xF
    
    matches = sum(1 for d in data if fletcher_mod16(d['nibbles_14']) == d['p'])
    print(f"Fletcher XOR: {matches}/{len(data)} ({matches/len(data)*100:.1f}%)")
    
    matches = sum(1 for d in data if ((fletcher_mod16(d['nibbles_14']) << 2) | (fletcher_mod16(d['nibbles_14']) >> 2)) & 0xF == d['p'])
    print(f"Fletcher ROL: {matches}/{len(data)} ({matches/len(data)*100:.1f}%)")
    
    # Provar Adler-like
    print("\nProvant Adler-like...")
    def adler_nibbles(nibbles):
        a = 1
        b = 0
        for nib in nibbles:
            a = (a + nib) & 0xF
            b = (b + a) & 0xF
        return b
    
    matches = sum(1 for d in data if adler_nibbles(d['nibbles_14']) == d['p'])
    print(f"Adler: {matches}/{len(data)} ({matches/len(data)*100:.1f}%)")
    
    # Provant Luhn-like
    print("\nProvant Luhn-like...")
    def luhn_nibbles(nibbles):
        total = 0
        for i, nib in enumerate(nibbles):
            if i % 2 == 0:
                doubled = nib * 2
                total += (doubled // 16) + (doubled % 16)
            else:
                total += nib
        return (10 - (total % 10)) % 10
    
    matches = sum(1 for d in data if (luhn_nibbles(d['nibbles_14']) & 0xF) == d['p'])
    print(f"Luhn: {matches}/{len(data)} ({matches/len(data)*100:.1f}%)")
    
    # Provar XOR amb multiplicacions
    print("\nProvant hash multiplicatiu...")
    
    for multiplier in [3, 5, 7, 11, 13]:
        matches = 0
        for d in data:
            h = 0
            for nib in d['nibbles_14']:
                h = ((h * multiplier) + nib) & 0xF
            if h == d['p']:
                matches += 1
        
        if matches / len(data) > 0.1:
            print(f"Hash mult={multiplier}: {matches}/{len(data)} ({matches/len(data)*100:.1f}%)")

if __name__ == "__main__":
    test_advanced_algorithms()
