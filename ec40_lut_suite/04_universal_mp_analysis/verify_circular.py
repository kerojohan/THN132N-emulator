#!/usr/bin/env python3
"""
Verificació: nibbles[0:15] inclou P?
"""

# Exemple
payload = "ec4013029410239e"
nibbles = [int(c, 16) for c in payload]

print(f"Payload: {payload}")
print(f"Nibbles: {[f'{n:X}' for n in nibbles]}")
print(f"Posicions: {list(range(16))}\n")

print(f"nibbles[0:15] =  {[f'{n:X}' for n in nibbles[0:15]]}")
print(f"  (posicions 0-14, que SÍ inclou P a pos 14!)\n")

print(f"P està a la posició 14: {nibbles[14]:X}")
print(f"nibbles[0:15] inclou fins la posició 14: True")
print(f"\nPer tant, estic calculant P com a funció de SI MATEIX!")
print(f"Això NO és una fórmula generadora útil.")
