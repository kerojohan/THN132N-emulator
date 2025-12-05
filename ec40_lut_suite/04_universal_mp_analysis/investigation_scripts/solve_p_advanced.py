#!/usr/bin/env python3
"""
Solver Avançat de Força Bruta per P.
Prova CRC-8 exhaustiu, CRC-4, Sumes Ponderades i LFSR.
"""

import csv
import time
from pathlib import Path
from collections import namedtuple

BASE_DIR = Path(__file__).parent.parent
CSV_FILE = BASE_DIR / "ec40_live.csv"

def get_nibbles(hex_str):
    return [int(c, 16) for c in hex_str]

def load_data():
    data = []
    with open(CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = row['raw64']
            checksum_hex = row['checksum_hex']
            
            if not raw or not checksum_hex: continue
            try:
                # Raw: payload + checksum
                # Checksum: 3 nibbles at end
                # P is last nibble
                payload_str = raw[:12] # 12 nibbles payload
                payload_nibbles = get_nibbles(payload_str)
                target_p = int(checksum_hex[-1], 16)
                
                # També guardem versió bytes
                payload_bytes = []
                for i in range(0, len(payload_nibbles), 2):
                    payload_bytes.append((payload_nibbles[i] << 4) | payload_nibbles[i+1])
                
                data.append({
                    'nibbles': payload_nibbles,
                    'bytes': payload_bytes,
                    'target': target_p
                })
            except:
                continue
    return data

# --- ALGORITMES ---

def crc8_full(data, poly, init, xor_out, ref_in, ref_out):
    crc = init
    for byte in data:
        if ref_in:
            byte = int('{:08b}'.format(byte)[::-1], 2)
        
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
        crc &= 0xFF
        
    if ref_out:
        crc = int('{:08b}'.format(crc)[::-1], 2)
        
    return (crc ^ xor_out) & 0xFF

def crc4_nibble(data, poly, init, xor_out):
    crc = init
    for nibble in data:
        crc ^= nibble
        for _ in range(4):
            if crc & 0x8:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
        crc &= 0xF
    return (crc ^ xor_out) & 0xF

def weighted_sum(data, k1, k2):
    s = 0
    for i, nibble in enumerate(data):
        s += nibble * (i * k1 + k2)
    return s & 0xF

# --- SOLVER ---

def solve(data):
    print(f"Iniciant Força Bruta Avançada amb {len(data)} mostres...")
    start_time = time.time()
    
    # 1. CRC-8 Exhaustiu (Bytes)
    # Espai: 256 (poly) * 256 (init) * 16 (xor_out 4 bits rellevants per P?) * 4 (ref in/out)
    # Reduïm espai: XOR out només afecta resultat final. Si trobem CRC que dóna P ^ K constant, ja val.
    # Així que XOR out = 0.
    # Només mirem si (CRC & 0xF) == Target o ((CRC >> 4) & 0xF) == Target
    
    print("\n[1/4] CRC-8 Exhaustiu...")
    best_score = 0
    
    # Optimització: Precalcular bytes
    bytes_list = [d['bytes'] for d in data]
    targets = [d['target'] for d in data]
    
    for poly in range(256):
        if poly % 32 == 0: print(f"  Poly 0x{poly:X}...")
        
        for init in range(256):
            for ref_config in range(4): # 00, 01, 10, 11
                ref_in = bool(ref_config & 1)
                ref_out = bool(ref_config & 2)
                
                matches_lo = 0
                matches_hi = 0
                
                # Check consistency (XOR constant)
                # Si (Calc ^ Target) és constant, hem trobat la fórmula (amb XOR Out = constant)
                diffs_lo = set()
                diffs_hi = set()
                
                valid = True
                for i in range(len(bytes_list)):
                    c = crc8_full(bytes_list[i], poly, init, 0, ref_in, ref_out)
                    
                    d_lo = (c & 0xF) ^ targets[i]
                    d_hi = ((c >> 4) & 0xF) ^ targets[i]
                    
                    diffs_lo.add(d_lo)
                    diffs_hi.add(d_hi)
                    
                    if len(diffs_lo) > 1 and len(diffs_hi) > 1:
                        valid = False
                        break
                
                if valid:
                    if len(diffs_lo) == 1:
                        xor_val = list(diffs_lo)[0]
                        print(f"  ✨ CRC-8 TROBAT (Lo)! Poly=0x{poly:X}, Init=0x{init:X}, RefIn={ref_in}, RefOut={ref_out}, XOR_Out=0x{xor_val:X}")
                        return
                    if len(diffs_hi) == 1:
                        xor_val = list(diffs_hi)[0]
                        print(f"  ✨ CRC-8 TROBAT (Hi)! Poly=0x{poly:X}, Init=0x{init:X}, RefIn={ref_in}, RefOut={ref_out}, XOR_Out=0x{xor_val:X}")
                        return

    # 2. CRC-4 Exhaustiu (Nibbles)
    print("\n[2/4] CRC-4 Exhaustiu...")
    nibbles_list = [d['nibbles'] for d in data]
    
    for poly in range(16):
        for init in range(16):
            diffs = set()
            valid = True
            for i in range(len(nibbles_list)):
                c = crc4_nibble(nibbles_list[i], poly, init, 0)
                d = c ^ targets[i]
                diffs.add(d)
                if len(diffs) > 1:
                    valid = False
                    break
            
            if valid:
                xor_val = list(diffs)[0]
                print(f"  ✨ CRC-4 TROBAT! Poly=0x{poly:X}, Init=0x{init:X}, XOR_Out=0x{xor_val:X}")
                return

    # 3. Suma Ponderada
    print("\n[3/4] Suma Ponderada...")
    for k1 in range(16):
        for k2 in range(16):
            diffs = set()
            valid = True
            for i in range(len(nibbles_list)):
                s = weighted_sum(nibbles_list[i], k1, k2)
                d = s ^ targets[i]
                diffs.add(d)
                if len(diffs) > 1:
                    valid = False
                    break
            
            if valid:
                xor_val = list(diffs)[0]
                print(f"  ✨ SUMA PONDERADA TROBADA! K1={k1}, K2={k2}, XOR_Out=0x{xor_val:X}")
                return

    print(f"\nFinalitzat en {time.time() - start_time:.2f}s sense èxit total.")

if __name__ == "__main__":
    data = load_data()
    solve(data)
