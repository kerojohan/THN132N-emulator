#!/usr/bin/env python3
import json
import pandas as pd
from collections import Counter

MERGED_FILE = "ec40_capturas_merged.csv"

def main():
    try:
        df = pd.read_csv(MERGED_FILE)
    except Exception as e:
        print(f"Error leyendo {MERGED_FILE}: {e}")
        return

    required_cols = {"temperature_C", "R12"}
    if not required_cols.issubset(df.columns):
        print(f"Faltan columnas en {MERGED_FILE}. Necesito: {required_cols}")
        return

    # Normalizar temperatura a pasos de 0.1 ºC
    df["temp_0_1"] = df["temperature_C"].round(1)

    lut = {}
    conflicts = []

    for temp, group in df.groupby("temp_0_1"):
        # Contar ocurrencias de cada R12 para esta temperatura
        c = Counter(group["R12"])
        most_common = c.most_common()

        if len(most_common) == 0:
            continue

        # Elegimos el más frecuente
        r12_best, count_best = most_common[0]

        # Si hay más de un valor, lo anotamos como conflicto
        if len(most_common) > 1:
            conflicts.append((temp, most_common))

        lut[str(float(temp))] = r12_best  # clave como string para JSON

    # Mostrar un pequeño resumen
    print("Temperaturas en LUT:", len(lut))
    print("Ejemplo (primeras 10):")
    for i, (t, r) in enumerate(sorted(lut.items(), key=lambda x: float(x[0]))):
        if i >= 10:
            break
        print(f"  {t} °C -> {r}")

    if conflicts:
        print("\nATENCIÓN: Conflictos detectados (R12 distintos para la misma temperatura):")
        for temp, values in conflicts:
            print(f"  Temp {temp} °C:")
            for r12_val, cnt in values:
                print(f"    {r12_val}  ({cnt} veces)")
    else:
        print("\nSin conflictos: cada temperatura tiene un único R12 observado.")

    # Guardar LUT en JSON
    with open("r12_lut.json", "w", encoding="utf-8") as f:
        json.dump(lut, f, indent=2, sort_keys=True)
    print("\nLUT guardada en r12_lut.json")

    # Guardar LUT como módulo Python
    with open("r12_lut.py", "w", encoding="utf-8") as f:
        f.write("# LUT auto-generada: temperatura (str) en °C -> R12 (hex string)\n")
        f.write("R12_LUT = {\n")
        for t, r in sorted(lut.items(), key=lambda x: float(x[0])):
            f.write(f"    {t!r}: {r!r},\n")
        f.write("}\n")
    print("LUT guardada en r12_lut.py (dict R12_LUT)")

if __name__ == "__main__":
    main()
