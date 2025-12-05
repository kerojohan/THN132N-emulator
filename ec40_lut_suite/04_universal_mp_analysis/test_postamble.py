#!/usr/bin/env python3
"""
Investiga el nibble postamble - és un checksum?
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def test_postamble_hypotheses():
    data = []
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                payload_hex = row['payload64_hex']
                nibbles = [int(c, 16) for c in payload_hex]
                
                postamble_actual = nibbles[15]
                
                data.append({
                    'nibbles': nibbles,
                    'postamble': postamble_actual
                })
                
            except (ValueError, KeyError):
                continue
    
    print(f"Testant hip`òtesis per postamble ({len(data)} mostres)...\n")
    
    # 1. Suma dels primers 15 nibbles
    matches = sum(1 for d in data if (sum(d['nibbles'][:15]) & 0xF) == d['postamble'])
    print(f"Sum(nibbles[0:15]) & 0xF: {matches}/{len(data)} ({matches/len(data)*100:.1f}%)")
    
    # 2. XOR dels primers 15 nibbles
    matches = 0
    for d in data:
        h = 0
        for nibble in d['nibbles'][:15]:
            h = ((h << 4) ^ nibble) & 0xFF
        h &= 0xF
        if h == d['postamble']: matches += 1
    print(f"XOR_accumulator(nibbles[0:15]) & 0xF: {matches}/{len(data)} ({matches/len(data)*100:.1f}%)")
    
    # 3. Diferent combinació
    matches_simple_xor = sum(1 for d in data if (sum([n for i,n in enumerate(d['nibbles'][:15]) if i % 2 == 0]) ^ sum([n for i,n in enumerate(d['nibbles'][:15]) if i % 2 == 1])) & 0xF == d['postamble'])
    print(f"XOR(sum_even, sum_odd): {matches_simple_xor}/{len(data)} ({matches_simple_xor/len(data)*100:.1f}%)")
    
    # 4. Checksum sobre tot incloent R1, M, P
    matches = sum(1 for d in data if (sum(d['nibbles'][:15]) & 0xF) == d['postamble'])
    print(f"Sum(all_except_postamble) & 0xF: {matches}/{len(data)} ({matches/len(data)*100:.1f}%)")
    
    # 5. Test específic: Postamble = (~Sum) & 0xF
    matches = sum(1 for d in data if ((~sum(d['nibbles'][:15])) & 0xF) == d['postamble'])
    print(f"(~Sum(nibbles[0:15])) & 0xF: {matches}/{len(data)} ({matches/len(data)*100:.1f}%)")
    
    # 6. Algoritme similar a P però aplicat als primers 15
    matches = 0
    for d in data:
        h = 0
        for nibble in d['nibbles'][:15]:
            h ^= nibble
        if h == d['postamble']: matches += 1
    print(f"Simple XOR: {matches}/{len(data)} ({matches/len(data)*100:.1f}%)")
    
    # 7. Provem CRC-4
    for poly in range(16):
        matches = 0
        for d in data:
            crc = 0
            for nibble in d['nibbles'][:15]:
                crc ^= nibble
                for _ in range(4):
                    if crc & 0x8:
                        crc = ((crc << 1) ^ poly) & 0xF
                    else:
                        crc = (crc << 1) & 0xF
            if crc == d['postamble']: matches += 1
            
        if matches / len(data) > 0.9:
            print(f"CRC-4 Poly 0x{poly:X}: {matches}/{len(data)} ({matches/len(data)*100:.1f}%)")

if __name__ == "__main__":
    test_postamble_hypotheses()
