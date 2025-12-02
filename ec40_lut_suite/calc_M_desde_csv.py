#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Calcula la tabla M[e] a partir de un CSV con todas las tramas EC40.

Formato esperado de cada línea (sin o con cabecera):
timestamp, raw168, ec40_hex, temp_C, canal, house, [b3_low_hex], [b7_hex], [r12_hex]

Ejemplo de línea:
2025-11-20 19:43:37,5555...,ec4017f21220c31b,22.1,1,247,0x2,0x1B,0x21B

Si las columnas b3_low / b7 / r12 no existen, el script calcula R12
a partir del campo ec40_hex (msg[3] & 0x0F y msg[7]).
"""

import csv
import sys
from collections import Counter

# -------------------------
# Tabla P[d] fija (d = 0..9)
# -------------------------
P = [
    0x000,  # P[0]
    0x075,  # P[1]
    0x0EA,  # P[2]
    0x09F,  # P[3]
    0x0B5,  # P[4]
    0x0C0,  # P[5]
    0x05F,  # P[6]
    0x02A,  # P[7]
    0x06B,  # P[8]
    0x01E,  # P[9]
]

def temp_to_e_d(temp_c: float):
    """
    Descompone una temperatura en ºC en:
      - e: parte entera tipo Oregon (truncado hacia 0)
      - d: décima (0..9), usando el truco de valor absoluto

    Ejemplo:
      - 18.3  -> e = 18, d = 3
      - -10.7 -> e = -10, d = 7
    """
    e = int(temp_c)  # truncado hacia 0
    # décima positiva
    t10 = int(round(abs(temp_c * 10)))
    d = t10 - abs(e) * 10
    if d < 0 or d > 9:
        # Puede pasar por redondeos raros, lo descartamos
        raise ValueError(f"décima fuera de rango para temp={temp_c}: d={d}")
    return e, d

def r12_from_ec40(ec40_hex: str) -> int:
    """
    Calcula R12 a partir de la trama EC40 (8 bytes en hex).
    R12 = ((msg[3] & 0x0F) << 8) | msg[7]
    """
    ec40_hex = ec40_hex.strip()
    if len(ec40_hex) < 16:
        raise ValueError(f"Trama EC40 demasiado corta: {ec40_hex}")
    msg = bytes.fromhex(ec40_hex)
    if len(msg) < 8:
        raise ValueError(f"EC40 no tiene 8 bytes: {ec40_hex}")
    b3_low = msg[3] & 0x0F
    b7 = msg[7]
    return ((b3_low << 8) | b7) & 0xFFF


def main(csv_path: str):
    # Diccionario e -> Counter de M candidatos
    M_candidates = {}

    with open(csv_path, newline='') as f:
        reader = csv.reader(f)
        first = True
        for row in reader:
            if not row:
                continue

            # Detectar cabecera: si tercera o cuarta columna no parecen hex/float, saltar
            if first:
                first = False
                # Heurística simple: si row[3] no es float, asumimos cabecera
                try:
                    float(row[3])
                except Exception:
                    # es cabecera, saltamos y seguimos
                    continue

            # Dependiendo de tu CSV, ajusta índices si hiciera falta:
            #  0: timestamp
            #  1: raw168
            #  2: ec40_hex
            #  3: temp_C
            #  4: canal
            #  5: house
            #  6: b3_low_hex (opcional)
            #  7: b7_hex (opcional)
            #  8: r12_hex (opcional)

            try:
                temp_str = row[3].strip()
                temp_c = float(temp_str)
            except Exception:
                # Línea rara, la saltamos
                continue

            try:
                e, d = temp_to_e_d(temp_c)
            except ValueError:
                continue

            # Intentar obtener R12:
            r12 = None

            # Si hay una columna r12 explícita en hex (tipo 0x21B)
            if len(row) >= 9 and row[8].strip().startswith("0x"):
                try:
                    r12 = int(row[8].strip(), 16) & 0xFFF
                except Exception:
                    r12 = None

            # Si no hay, lo calculamos a partir de la EC40
            if r12 is None:
                ec40_hex = row[2]
                try:
                    r12 = r12_from_ec40(ec40_hex)
                except Exception:
                    continue

            # Comprobar d en rango P
            if d < 0 or d >= len(P):
                continue

            # Candidato para M[e]
            M_val = r12 ^ P[d]

            if e not in M_candidates:
                M_candidates[e] = Counter()
            M_candidates[e][M_val] += 1

    # Ahora elegimos para cada e el valor de M más frecuente
    M_final = {}
    for e, counter in M_candidates.items():
        # value with highest count
        val, cnt = counter.most_common(1)[0]
        M_final[e] = val

    # Imprimir tabla ordenada
    print("# Tabla M[e] reconstruida a partir de", csv_path)
    for e in sorted(M_final.keys()):
        print(f"{e:>4} : 0x{M_final[e]:03X}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 calc_M_desde_csv.py ec40_capturas_merged.csv")
    else:
        main(sys.argv[1])

