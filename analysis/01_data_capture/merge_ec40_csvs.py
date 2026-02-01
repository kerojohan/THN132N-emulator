#!/usr/bin/env python3
import glob
import os
import pandas as pd

def main():
    # Buscar todos los CSV tipo ec40_capturas*.csv
    files = sorted(glob.glob("ec40_capturas*.csv"))
    if not files:
        print("No se encontraron ficheros ec40_capturas*.csv")
        return

    print("Encontrados CSV:")
    for f in files:
        print("  -", f)

    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f)
            df["source_file"] = os.path.basename(f)
            dfs.append(df)
        except Exception as e:
            print(f"Error leyendo {f}: {e}")

    if not dfs:
        print("No hay datos válidos.")
        return

    all_df = pd.concat(dfs, ignore_index=True)

    # Eliminar duplicados exactos (misma fila completa)
    before = len(all_df)
    all_df = all_df.drop_duplicates()
    after = len(all_df)
    print(f"Filas totales: {before}, tras eliminar duplicados: {after}")

    # Ordenar por timestamp si existe
    if "timestamp" in all_df.columns:
        all_df["timestamp"] = pd.to_datetime(all_df["timestamp"], errors="coerce")
        all_df = all_df.sort_values("timestamp").reset_index(drop=True)

    out_file = "ec40_capturas_merged.csv"
    all_df.to_csv(out_file, index=False)
    print(f"Fichero unificado guardado en: {out_file}")

if __name__ == "__main__":
    main()
