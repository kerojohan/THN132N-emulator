#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Recalcula las tablas M y P a partir de las tramas capturadas EC40.

Este script:
1. Filtra tramas que empiezan con el preámbulo conocido (555555559995a5a6aa6a)
2. Calcula la tabla P[d] (d = 0..9) para cada décima de temperatura
3. Calcula la tabla M[e] para cada temperatura entera
4. Genera documentación con las tablas resultantes
"""

import csv
import sys
from collections import Counter, defaultdict
from typing import Dict, Tuple, List

# Preámbulo conocido de Oregon Scientific v2.1 para THN132N
KNOWN_PREAMBLE = "555555559995a5a6aa6a"


def temp_to_e_d(temp_c: float) -> Tuple[int, int]:
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


def filter_valid_frames(csv_path: str) -> List[Tuple[float, int, str]]:
    """
    Lee el CSV y filtra las tramas que empiezan con el preámbulo conocido.
    
    Returns:
        Lista de tuplas (temperatura_C, R12, raw168_hex)
    """
    valid_frames = []
    skipped_count = 0
    
    with open(csv_path, newline='') as f:
        reader = csv.reader(f)
        first = True
        
        for row in reader:
            if not row:
                continue
            
            # Detectar cabecera
            if first:
                first = False
                try:
                    float(row[3])
                except Exception:
                    # es cabecera, saltamos
                    continue
            
            # Formato esperado:
            # 0: timestamp
            # 1: raw168_hex
            # 2: payload64_hex (ec40)
            # 3: temperature_C
            # 4: channel
            # 5: house
            # 6: b3_low
            # 7: b7
            # 8: R12
            
            raw168_hex = row[1].strip().lower()
            
            # Filtrar por preámbulo
            if not raw168_hex.startswith(KNOWN_PREAMBLE.lower()):
                skipped_count += 1
                continue
            
            try:
                temp_c = float(row[3].strip())
            except Exception:
                continue
            
            # Obtener R12
            r12 = None
            if len(row) >= 9 and row[8].strip().startswith("0x"):
                try:
                    r12 = int(row[8].strip(), 16) & 0xFFF
                except Exception:
                    r12 = None
            
            # Si no hay R12 explícito, calcularlo desde ec40
            if r12 is None:
                ec40_hex = row[2]
                try:
                    r12 = r12_from_ec40(ec40_hex)
                except Exception:
                    continue
            
            valid_frames.append((temp_c, r12, raw168_hex))
    
    print(f"Tramas válidas (con preámbulo correcto): {len(valid_frames)}")
    print(f"Tramas descartadas (sin preámbulo correcto): {skipped_count}")
    
    return valid_frames


def calculate_P_table(frames: List[Tuple[float, int, str]], iterations: int = 5) -> Dict[int, int]:
    """
    Calcula la tabla P[d] para cada décima (d = 0..9) usando un enfoque iterativo.
    
    Estrategia iterativa:
    1. Inicializar P[d] = 0 para todos los d
    2. Calcular M[e] = R12 ^ P[d] más frecuente para cada e
    3. Recalcular P[d] = R12 ^ M[e] más frecuente para cada d
    4. Repetir hasta convergencia
    """
    # Inicializar P[d] = 0
    P_table = {d: 0x000 for d in range(10)}
    
    for iteration in range(iterations):
        # Calcular M[e] usando P[d] actual
        M_candidates = defaultdict(Counter)
        
        for temp_c, r12, _ in frames:
            try:
                e, d = temp_to_e_d(temp_c)
            except ValueError:
                continue
            
            # M[e] = R12 ^ P[d]
            m_val = r12 ^ P_table[d]
            M_candidates[e][m_val] += 1
        
        # Elegir M[e] más frecuente
        M_table = {}
        for e, counter in M_candidates.items():
            val, cnt = counter.most_common(1)[0]
            M_table[e] = val
        
        # Recalcular P[d] usando M[e]
        P_candidates = defaultdict(Counter)
        
        for temp_c, r12, _ in frames:
            try:
                e, d = temp_to_e_d(temp_c)
            except ValueError:
                continue
            
            if e not in M_table:
                continue
            
            # P[d] = R12 ^ M[e]
            p_val = r12 ^ M_table[e]
            P_candidates[d][p_val] += 1
        
        # Actualizar P[d] con el valor más frecuente
        new_P_table = {}
        for d in range(10):
            if d in P_candidates and len(P_candidates[d]) > 0:
                val, cnt = P_candidates[d].most_common(1)[0]
                new_P_table[d] = val
            else:
                new_P_table[d] = P_table[d]  # mantener valor anterior
        
        # Verificar convergencia
        if new_P_table == P_table:
            print(f"  Convergencia alcanzada en iteración {iteration + 1}")
            break
        
        P_table = new_P_table
    
    return P_table


def calculate_M_table(frames: List[Tuple[float, int, str]], P_table: Dict[int, int]) -> Dict[int, int]:
    """
    Calcula la tabla M[e] usando la tabla P[d] conocida.
    
    Para cada temperatura entera e:
    M[e] = R12 ^ P[d]
    """
    M_candidates = defaultdict(Counter)
    
    for temp_c, r12, _ in frames:
        try:
            e, d = temp_to_e_d(temp_c)
        except ValueError:
            continue
        
        if d not in P_table:
            continue
        
        # M[e] = R12 ^ P[d]
        m_val = r12 ^ P_table[d]
        M_candidates[e][m_val] += 1
    
    # Elegir el valor más frecuente para cada M[e]
    M_table = {}
    for e, counter in M_candidates.items():
        val, cnt = counter.most_common(1)[0]
        M_table[e] = val
    
    return M_table


def verify_tables(frames: List[Tuple[float, int, str]], M_table: Dict[int, int], P_table: Dict[int, int]):
    """
    Verifica que las tablas M y P generan correctamente los valores R12 observados.
    """
    errors = []
    correct = 0
    
    for temp_c, r12_observed, raw168 in frames:
        try:
            e, d = temp_to_e_d(temp_c)
        except ValueError:
            continue
        
        if e not in M_table or d not in P_table:
            continue
        
        r12_calculated = M_table[e] ^ P_table[d]
        
        if r12_calculated == r12_observed:
            correct += 1
        else:
            errors.append({
                'temp': temp_c,
                'e': e,
                'd': d,
                'r12_observed': r12_observed,
                'r12_calculated': r12_calculated,
                'M[e]': M_table[e],
                'P[d]': P_table[d]
            })
    
    print(f"\nVerificación:")
    print(f"  Tramas correctas: {correct}")
    print(f"  Tramas con error: {len(errors)}")
    
    if errors:
        print(f"\nPrimeros 10 errores:")
        for i, err in enumerate(errors[:10]):
            print(f"  {i+1}. Temp={err['temp']}°C (e={err['e']}, d={err['d']})")
            print(f"     R12 observado: 0x{err['r12_observed']:03X}")
            print(f"     R12 calculado: 0x{err['r12_calculated']:03X}")
            print(f"     M[{err['e']}]=0x{err['M[e]']:03X}, P[{err['d']}]=0x{err['P[d]']:03X}")
    
    return correct, len(errors)


def generate_documentation(M_table: Dict[int, int], P_table: Dict[int, int], 
                          csv_path: str, total_frames: int, correct: int, errors: int):
    """
    Genera un documento markdown con las tablas M y P.
    """
    doc_path = "tablas_M_P_recalculadas.md"
    
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write("# Tablas M y P Recalculadas\n\n")
        f.write(f"**Fecha de generación:** {csv_path}\n\n")
        f.write(f"**Tramas analizadas:** {total_frames}\n")
        f.write(f"**Tramas correctas:** {correct}\n")
        f.write(f"**Tramas con error:** {errors}\n")
        f.write(f"**Precisión:** {100*correct/(correct+errors):.2f}%\n\n")
        
        f.write("## Tabla P[d] - Décimas de temperatura\n\n")
        f.write("| d | P[d] (hex) | P[d] (dec) |\n")
        f.write("|---|------------|------------|\n")
        for d in range(10):
            if d in P_table:
                f.write(f"| {d} | 0x{P_table[d]:03X} | {P_table[d]:4d} |\n")
        
        f.write("\n## Tabla M[e] - Temperaturas enteras\n\n")
        f.write("| e (°C) | M[e] (hex) | M[e] (dec) |\n")
        f.write("|--------|------------|------------|\n")
        for e in sorted(M_table.keys()):
            f.write(f"| {e:4d} | 0x{M_table[e]:03X} | {M_table[e]:4d} |\n")
        
        f.write("\n## Código Python - Tabla P\n\n")
        f.write("```python\n")
        f.write("P_TABLE = [\n")
        for d in range(10):
            if d in P_table:
                f.write(f"    0x{P_table[d]:03X},  # P[{d}]\n")
        f.write("]\n")
        f.write("```\n\n")
        
        f.write("## Código Python - Tabla M\n\n")
        f.write("```python\n")
        f.write("M_TABLE = {\n")
        for e in sorted(M_table.keys()):
            f.write(f"    {e:4d}: 0x{M_table[e]:03X},\n")
        f.write("}\n")
        f.write("```\n\n")
        
        f.write("## Fórmula de cálculo\n\n")
        f.write("Para una temperatura `T` en °C:\n\n")
        f.write("1. Descomponer: `e = int(T)`, `d = int(abs(T * 10)) % 10`\n")
        f.write("2. Calcular: `R12 = M[e] ^ P[d]`\n")
        f.write("3. El valor R12 se codifica en los bytes 3 y 7 del mensaje EC40\n\n")
    
    print(f"\nDocumentación generada en: {doc_path}")


def main(csv_path: str):
    print(f"Analizando: {csv_path}")
    print(f"Preámbulo requerido: {KNOWN_PREAMBLE}\n")
    
    # 1. Filtrar tramas válidas
    frames = filter_valid_frames(csv_path)
    
    if not frames:
        print("ERROR: No se encontraron tramas válidas")
        return
    
    # 2. Calcular tabla P
    print("\nCalculando tabla P[d]...")
    P_table = calculate_P_table(frames)
    
    print("Tabla P[d]:")
    for d in range(10):
        if d in P_table:
            print(f"  P[{d}] = 0x{P_table[d]:03X}")
    
    # 3. Calcular tabla M usando P
    print("\nCalculando tabla M[e]...")
    M_table = calculate_M_table(frames, P_table)
    
    print(f"Tabla M[e] calculada para {len(M_table)} temperaturas enteras")
    print("Ejemplo (primeras 10):")
    for i, e in enumerate(sorted(M_table.keys())[:10]):
        print(f"  M[{e:4d}] = 0x{M_table[e]:03X}")
    
    # 4. Verificar tablas
    print("\nVerificando tablas...")
    correct, errors = verify_tables(frames, M_table, P_table)
    
    # 5. Generar documentación
    generate_documentation(M_table, P_table, csv_path, len(frames), correct, errors)
    
    print("\n¡Proceso completado!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 recalc_M_P_tables.py ec40_capturas_merged.csv")
        sys.exit(1)
    
    main(sys.argv[1])
