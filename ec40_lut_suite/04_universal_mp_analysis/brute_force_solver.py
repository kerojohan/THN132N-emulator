#!/usr/bin/env python3
"""
Solver de Força Bruta per trobar les fórmules de generació de M i P.
Genera i avalua milers d'hipòtesis matemàtiques.
"""

import csv
import time
import operator
from pathlib import Path
from collections import namedtuple
import itertools

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "04_universal_mp_analysis" / "golden_master.csv"

# Estructura de dades
Record = namedtuple('Record', ['h', 't', 'm', 'p'])

def load_data():
    data = []
    with open(DATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(Record(
                h=int(row['house']),
                t=int(row['temp_idx']),
                m=int(row['m']),
                p=int(row['p'])
            ))
    return data

# --- PRIMITIVES ---

def get_h_key(h): return h & 0x0B
def get_h_lo(h): return h & 0x0F
def get_h_hi(h): return (h >> 4) & 0xF

# Operacions
OPS = {
    'XOR': operator.xor,
    'AND': operator.and_,
    'OR': operator.or_,
    'ADD': lambda a, b: (a + b) & 0xF, # Modulo 16 per resultats de 4 bits
    'SUB': lambda a, b: (a - b) & 0xF,
}

# --- GENERADOR D'HIPÒTESIS ---

class Hypothesis:
    def __init__(self, name, func):
        self.name = name
        self.func = func

    def evaluate(self, record, target_attr):
        try:
            val = self.func(record)
            return (val & 0xF) == getattr(record, target_attr)
        except:
            return False

def generate_m_hypotheses():
    """Genera hipòtesis per M"""
    hyps = []
    
    # 1. Hipòtesis basades en desplaçament de T (T >> S)
    # M sovint és una part alta de la temperatura
    for shift in range(1, 9):
        # Directe: M = (T >> shift)
        hyps.append(Hypothesis(f"(T >> {shift})", 
                               lambda r, s=shift: (r.t >> s)))
        
        # Amb XOR House Key: M = (T >> shift) ^ H_key
        hyps.append(Hypothesis(f"(T >> {shift}) ^ H_key", 
                               lambda r, s=shift: (r.t >> s) ^ get_h_key(r.h)))
        
        # Amb XOR House Lo: M = (T >> shift) ^ H_lo
        hyps.append(Hypothesis(f"(T >> {shift}) ^ H_lo", 
                               lambda r, s=shift: (r.t >> s) ^ get_h_lo(r.h)))
                               
        # Amb XOR Constant: M = (T >> shift) ^ K
        for k in range(16):
            hyps.append(Hypothesis(f"(T >> {shift}) ^ {k}", 
                                   lambda r, s=shift, k=k: (r.t >> s) ^ k))
            
            # Combinat: M = (T >> shift) ^ H_key ^ K
            hyps.append(Hypothesis(f"(T >> {shift}) ^ H_key ^ {k}", 
                                   lambda r, s=shift, k=k: (r.t >> s) ^ get_h_key(r.h) ^ k))

    return hyps

def generate_p_hypotheses():
    """Genera hipòtesis per P (més complexes)"""
    hyps = []
    
    # P pot dependre de M
    # P = M ^ K
    for k in range(16):
        hyps.append(Hypothesis(f"M ^ {k}", lambda r, k=k: r.m ^ k))
        hyps.append(Hypothesis(f"M ^ H_lo ^ {k}", lambda r, k=k: r.m ^ get_h_lo(r.h) ^ k))
        hyps.append(Hypothesis(f"M ^ H_hi ^ {k}", lambda r, k=k: r.m ^ get_h_hi(r.h) ^ k))
    
    # P = (T >> S) ^ ...
    for shift in range(1, 9):
        for k in range(16):
            hyps.append(Hypothesis(f"(T >> {shift}) ^ {k}", 
                                   lambda r, s=shift, k=k: (r.t >> s) ^ k))
            hyps.append(Hypothesis(f"(T >> {shift}) ^ M ^ {k}", 
                                   lambda r, s=shift, k=k: (r.t >> s) ^ r.m ^ k))
            hyps.append(Hypothesis(f"(T >> {shift}) ^ H_lo ^ {k}", 
                                   lambda r, s=shift, k=k: (r.t >> s) ^ get_h_lo(r.h) ^ k))

    return hyps

# --- SOLVER ---

def solve(data, target='m', hypotheses=None):
    print(f"\nBuscant fórmula per '{target.upper()}' amb {len(hypotheses)} hipòtesis...")
    
    best_score = -1
    best_hyps = []
    
    start_time = time.time()
    
    for i, hyp in enumerate(hypotheses):
        matches = 0
        for record in data:
            if hyp.evaluate(record, target):
                matches += 1
        
        score = matches / len(data)
        
        if score > best_score:
            best_score = score
            best_hyps = [hyp]
            print(f"  Nova millor: {score*100:.1f}% -> {hyp.name}")
        elif score == best_score:
            best_hyps.append(hyp)
            
        if i % 1000 == 0 and i > 0:
            print(f"  ... {i} hipòtesis provades")
            
    elapsed = time.time() - start_time
    print(f"\nFinalitzat en {elapsed:.2f}s.")
    print(f"Millor puntuació: {best_score*100:.1f}%")
    print("Millors fórmules:")
    for h in best_hyps[:5]:
        print(f"  - {h.name}")
        
    return best_hyps

def main():
    data = load_data()
    print(f"Carregats {len(data)} registres.")
    
    # 1. Buscar M
    m_hyps = generate_m_hypotheses()
    solve(data, 'm', m_hyps)
    
    # 2. Buscar P
    p_hyps = generate_p_hypotheses()
    solve(data, 'p', p_hyps)

if __name__ == "__main__":
    main()
