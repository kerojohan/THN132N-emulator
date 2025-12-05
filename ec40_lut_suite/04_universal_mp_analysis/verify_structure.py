#!/usr/bin/env python3
"""
Analitza l'estructura EXACTA del payload.
"""

# Exemple real: ec4013029410239e
payload = "ec4013029410239e"
nibbles = [int(c, 16) for c in payload]

print("Posició | Hex | Decimal | Descripció")
print("--------|-----|---------|------------------")

# Basant-me en les captures
print(f"  0-3   | EC40|         | ID del sensor")
print(f"  {0}     | {nibbles[0]:X}   | {nibbles[0]:2d}      | E (ID MSN)")
print(f"  {1}     | {nibbles[1]:X}   | {nibbles[1]:2d}      | C (ID)")
print(f"  {2}     | {nibbles[2]:X}   | {nibbles[2]:2d}      | 4 (ID)")
print(f"  {3}     | {nibbles[3]:X}   | {nibbles[3]:2d}      | 0 (ID LSN)")
print(f"  {4}     | {nibbles[4]:X}   | {nibbles[4]:2d}      | Channel")
print(f"  {5}     | {nibbles[5]:X}   | {nibbles[5]:2d}      | House LSN")
print(f"  {6}     | {nibbles[6]:X}   | {nibbles[6]:2d}      | House MSN")
print(f"  {7}     | {nibbles[7]:X}   | {nibbles[7]:2d}      | Nibble 7 (VARIABLE!)")
print(f"  {8}     | {nibbles[8]:X}   | {nibbles[8]:2d}      | Temp LSN")
print(f"  {9}     | {nibbles[9]:X}   | {nibbles[9]:2d}      | Temp Mid")
print(f"  {10}     | {nibbles[10]:X}   | {nibbles[10]:2d}      | Temp MSN")
print(f"  {11}     | {nibbles[11]:X}   | {nibbles[11]:2d}      | Flags")
print(f"  {12}     | {nibbles[12]:X}   | {nibbles[12]:2d}      | R1")
print(f"  {13}     | {nibbles[13]:X}   | {nibbles[13]:2d}      | M")
print(f"  {14}     | {nibbles[14]:X}   | {nibbles[14]:2d}      | P")
print(f"  {15}     | {nibbles[15]:X}   | {nibbles[15]:2d}      | Postamble")

# Verificar temperatura
temp_bcd = f"{nibbles[10]}{nibbles[9]}{nibbles[8]}"
print(f"\nTemperatura BCD: {temp_bcd} =  {int(temp_bcd)/10:.1f}°C")

# Verificar House
house = (nibbles[6] << 4) | nibbles[5]
print(f"House Code: 0x{nibbles[6]:X}{nibbles[5]:X} = {house}")
