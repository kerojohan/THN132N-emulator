#!/usr/bin/env python3
"""
Nova hipòtesi: P i Postamble es calculen junts.
Provar si hi ha relació entre P i Postamble.
"""

import csv
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def analyze_p_postamble_relation():
    data = []
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                payload_hex = row['payload64_hex']
                nibbles = [int(c, 16) for c in payload_hex]
                
                data.append({
                    'nibbles_14': nibbles[:14],
                    'p': nibbles[14],
                    'postamble': nibbles[15]
                })
            except (ValueError, KeyError):
                continue
    
    print(f"Dataset: {len(data)} mostres\n")
    
    # Analitzar relació P vs Postamble
    print("Relació P vs Postamble:")
    
    p_post_pairs = Counter([(d['p'], d['postamble']) for d in data])
    print(f"\nParelles (P, Post) més comunes:")
    for (p, post), count in p_post_pairs.most_common(20):
        print(f"  P={p:X}, Post={post:X}: {count} vegades")
    
    # Provar operacions entre P i Postamble
    print(f"\nProvant si Postamble = f(P, ...):")
    
    # Test 1: Post = P XOR constant
    for const in range(16):
        matches = sum(1 for d in data if (d['p'] ^ const) == d['postamble'])
        if matches / len(data) > 0.9:
            print(f"✨ Post = P XOR 0x{const:X}: {matches}/{len(data)} ({matches/len(data)*100:.1f}%)")
    
    # Test 2: Post + P = constant
    sums = Counter([((d['p'] + d['postamble']) & 0xF) for d in data])
    print(f"\nDistribució (P + Post) & 0xF: {dict(sums)}")
    
    # Test 3: Post XOR P
    xors = Counter([(d['p'] ^ d['postamble']) for d in data])
    print(f"Distribució P XOR Post: {dict(xors)}")
    
    # Test 4: Provar si P+Post depèn dels primers 14 nibbles
    print(f"\nProvant si (P + Post) es calcula dels primers 14 nibbles...")
    
    # Simple sum
    matches = sum(1 for d in data if ((sum(d['nibbles_14']) & 0xF) == ((d['p'] + d['postamble']) & 0xF)))
    print(f"  Sum[0:14] == (P+Post): {matches}/{len(data)} ({matches/len(data)*100:.1f}%)")
    
    # XOR
    def simple_xor(nibbles):
        x = 0
        for n in nibbles:
            x ^= n
        return x & 0xF
    
    matches = sum(1 for d in data if (simple_xor(d['nibbles_14']) == ((d['p'] ^ d['postamble']) & 0xF)))
    print(f"  XOR[0:14] == (P XOR Post): {matches}/{len(data)} ({matches/len(data)*1008:.1f}%)")

if __name__ == "__main__":
    analyze_p_postamble_relation()
