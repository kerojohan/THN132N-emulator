#!/usr/bin/env python3
"""
FORÇA BRUTA COMPLETA: Prova TOTS els algoritmes possibles per P.
Sobre els primers 14 nibbles (sense P).
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "ec40_capturas_merged.csv"

def load_data_with_14_nibbles():
    """Carrega dades amb els primers 14 nibbles."""
    data = []
    
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                payload_hex = row['payload64_hex']
                nibbles = [int(c, 16) for c in payload_hex]
                
                # Els primers 14 nibbles (sense P ni postamble)
                nibbles_14 = nibbles[:14]
                p_real = nibbles[14]
                
                data.append({
                    'nibbles_14': nibbles_14,
                    'p': p_real
                })
                
            except (ValueError, KeyError):
                continue
    
    return data

def test_all_algorithms():
    data = load_data_with_14_nibbles()
    print(f"Dataset: {len(data)} mostres\n")
    
    algorithms = {}
    
    # 1. Sumes simples
    algorithms['Sum[0:14] & 0xF'] = lambda n: sum(n) & 0xF
    algorithms['Sum[0:12] & 0xF'] = lambda n: sum(n[:12]) & 0xF
    algorithms['Sum[8:14] & 0xF (temp+flags+R1+M)'] = lambda n: sum(n[8:14]) & 0xF
    
    # 2. XOR simple
    def simple_xor(nibbles):
        x = 0
        for nib in nibbles:
            x ^= nib
        return x & 0xF
    
    algorithms['XOR simple [0:14]'] = simple_xor
    algorithms['XOR simple [0:12]'] = lambda n: simple_xor(n[:12])
    
    # 3. XOR amb posicions parells/senars
    algorithms['XOR(even_pos)'] = lambda n: simple_xor([n[i] for i in range(0, 14, 2)])
    algorithms['XOR(odd_pos)'] = lambda n: simple_xor([n[i] for i in range(1, 14, 2)])
    
    # 4. Operacions sobre R1, M
    algorithms['R1 XOR M'] = lambda n: (n[12] ^ n[13]) & 0xF
    algorithms['R1 + M'] = lambda n: (n[12] + n[13]) & 0xF
    algorithms['R1 - M'] = lambda n: (n[12] - n[13]) & 0xF
    algorithms['~R1'] = lambda n: (~n[12]) & 0xF
    algorithms['~M'] = lambda n: (~n[13]) & 0xF
    
    # 5. Operacions sobre temperatura
    temp_sum = lambda n: (n[8] + n[9] + n[10]) & 0xF
    algorithms['Temp sum'] = temp_sum
    algorithms['Temp XOR'] = lambda n: (n[8] ^ n[9] ^ n[10]) & 0xF
    
    # 6. Combinacions
    algorithms['(R1 XOR M) + Temp'] = lambda n: ((n[12] ^ n[13]) + temp_sum(n)) & 0xF
    algorithms['Sum[0:12] XOR Sum[12:14]'] = lambda n: (sum(n[:12]) ^ sum(n[12:14])) & 0xF
    
    # 7. Nibble 7 involucrat
    algorithms['Nib7'] = lambda n: n[7]
    algorithms['Nib7 XOR R1'] = lambda n: (n[7] ^ n[12]) & 0xF
    algorithms['Nib7 XOR M'] = lambda n: (n[7] ^ n[13]) & 0xF
    algorithms['Nib7 XOR (R1+M)'] = lambda n: (n[7] ^ ((n[12] + n[13]) & 0xF)) & 0xF
    
    # 8. House involucrat
    algorithms['House_LSN XOR M'] = lambda n: (n[5] ^ n[13]) & 0xF
    algorithms['House_MSN XOR R1'] = lambda n: (n[6] ^ n[12]) & 0xF
    
    # 9. Checksum byte sencer
    algorithms['(Sum[0:14] >> 4) & 0xF'] = lambda n: (sum(n) >> 4) & 0xF
    algorithms['Sum[0:14] >> 8'] = lambda n: (sum(n) >> 8) & 0xF
    
    # 10. Rotacions
    algorithms['ROL(R1, 1)'] = lambda n: ((n[12] << 1) | (n[12] >> 3)) & 0xF
    algorithms['ROR(M, 1)'] = lambda n: ((n[13] >> 1) | (n[13] << 3)) & 0xF
    
    # Executar tots
    results = {}
    for name, func in algorithms.items():
        matches = 0
        for d in data:
            try:
                if func(d['nibbles_14']) == d['p']:
                    matches += 1
            except:
                pass
        
        results[name] = matches
    
    # Mostrar resultats
    print("Resultats (ordenats per precisió):\n")
    print(f"Algoritme                                  | Matches | Accuracy")
    print(f"-------------------------------------------|---------|----------")
    
    for name in sorted(results.keys(), key=lambda x: -results[x]):
        matches = results[name]
        acc = matches / len(data) * 100
        status = "✅" if acc > 99 else "⚠️" if acc > 90 else "🔍" if acc > 50 else "❌"
        
        if acc > 5:  # Només mostrar si >5%
            print(f"{status} {name:40s} | {matches:7d} | {acc:5.1f}%")

if __name__ == "__main__":
    test_all_algorithms()
