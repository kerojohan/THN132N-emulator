EC40 / THN132N - Tooling para cálculo de LUT R12
===============================================

Contenido:
  - merge_ec40_csvs.py
      Junta todos los ficheros ec40_capturas*.csv en uno solo:
          ec40_capturas_merged.csv

  - build_r12_lut.py
      Lee ec40_capturas_merged.csv, agrupa por temperatura_C (redondeada a 0.1 ºC)
      y calcula, para cada temperatura, el R12 más frecuente.
      Genera:
          - r12_lut.json  (LUT en JSON)
          - r12_lut.py    (módulo Python con dict R12_LUT)

  - use_r12_lut_example.py
      Ejemplo de cómo usar R12_LUT para obtener b3_low y b7 a partir de una temperatura.

Flujo típico:
  1) Ir capturando sesiones y guardarlas como:
        ec40_capturas.csv, ec40_capturas_2.csv, ec40_capturas_3.csv, ...

  2) Unificar:
        python3 merge_ec40_csvs.py

  3) Construir LUT:
        python3 build_r12_lut.py

  4) Usar LUT en tus scripts / generadores:
        from r12_lut import R12_LUT
        # ver use_r12_lut_example.py
