# oregon_parameters.py
# Parámetros y tablas para emular el sensor Oregon Scientific THN132N
# Generado a partir de análisis de capturas reales

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
# Puedes cambiar estos valores, pero las tablas M y P deben coincidir con el HOUSE_CODE
DEFAULT_HOUSE_CODE = 247  # 0xF7
DEFAULT_CHANNEL = 1

# ==============================================================================
# TABLAS BASE (Correspondientes a House Code 3)
# ==============================================================================
# Tabla P Base (décimas de grado 0-9)
P_TABLE_BASE = [
    0x075, 0x000, 0x09F, 0x0EA, 0x0C0, 
    0x0B5, 0x02A, 0x05F, 0x01E, 0x06B
]

# Tabla M (parte entera de temperatura)
# Mapea temperatura entera (e) -> valor M
M_TABLE = {
    -16: 0x2D4, -15: 0x227, -14: 0x276, -13: 0x2C0, -12: 0x291,
    -11: 0x262, -10: 0x233,  -9: 0x2EF,  -8: 0x2BE,  -7: 0x282,
     -6: 0x2D3,  -5: 0x220,  -4: 0x271,  -3: 0x2C7,  -2: 0x296,
     -1: 0x265,   0: 0x2B7,   1: 0x13D,   2: 0x1CE,   3: 0x19F,
      4: 0x129,   5: 0x178,   6: 0x18B,   7: 0x1DA,   8: 0x1E6,
      9: 0x1B7,  10: 0x16B,  11: 0x13A,  12: 0x1C9,  13: 0x243,
     14: 0x2F5,  15: 0x17F,  16: 0x18C,  17: 0x1DD,  18: 0x1E1,
     19: 0x813,  20: 0x2B9,  21: 0x133,  22: 0x1C0,  23: 0x191,
     24: 0x127,  25: 0x176,  26: 0x185,  27: 0x1D4,  28: 0x1E8,
     29: 0x1B9,  30: 0x165,  31: 0x134,  32: 0x1C7,  33: 0x196,
     34: 0x883,  35: 0x8D2,  36: 0x821,  37: 0x870,  38: 0x84C,
     39: 0x81D,  40: 0x8B3,  41: 0x8E2,  42: 0x811,  43: 0x840,
     44: 0x8F6,  45: 0x8A7,  46: 0x854,  47: 0x805,  48: 0x839,
     49: 0x868,  50: 0x117,  51: 0x146,  52: 0x816,  53: 0x1E4,
     54: 0x8F1,  56: 0x22B,  57: 0x1A1,  58: 0x246,  61: 0x14F
}

def get_p_table(house_code):
    """
    Devuelve la tabla P correcta para el house code dado.
    """
    if house_code == 3:
        return P_TABLE_BASE
    elif house_code == 247: # 0xF7
        # Para House 247, aplicamos XOR 0x075 a la tabla base
        return [x ^ 0x075 for x in P_TABLE_BASE]
    elif house_code == 96:  # 0x60
        # Patrón complejo para House 96
        return [0x01E, 0x01E, 0x0F4, 0x081, 0x0DE, 0x0DE, 0x034, 0x034, 0x000, 0x000]
    else:
        # Por defecto devolvemos la base, pero advertimos
        print(f"ADVERTENCIA: House Code {house_code} no caracterizado. Usando tabla base.")
        return P_TABLE_BASE

def calculate_r12(temp_c, house_code=DEFAULT_HOUSE_CODE):
    """
    Calcula el valor R12 para una temperatura y house code dados.
    """
    e = int(temp_c)
    # Obtener décima (0-9)
    d = int(round(abs(temp_c * 10))) - abs(e) * 10
    
    if d < 0 or d > 9:
        d = 0 # Fallback seguro
        
    if e not in M_TABLE:
        raise ValueError(f"Temperatura {temp_c}°C fuera de rango en tabla M")
        
    p_table = get_p_table(house_code)
    
    # R12 = M[e] XOR P[d]
    return M_TABLE[e] ^ p_table[d]

def encode_ec40_bytes(temp_c, house_code=DEFAULT_HOUSE_CODE, channel=DEFAULT_CHANNEL):
    """
    Genera los bytes clave para el mensaje EC40.
    Retorna: (byte3, byte7)
    """
    r12 = calculate_r12(temp_c, house_code)
    
    # Byte 3: Nibble alto = House Code (high), Nibble bajo = R12 (high)
    # Nota: El house code en el mensaje es solo el nibble alto del house code real
    house_nibble = (house_code >> 4) & 0x0F
    r12_high_nibble = (r12 >> 8) & 0x0F
    
    byte3 = (house_nibble << 4) | r12_high_nibble
    
    # Byte 7: R12 (low 8 bits)
    byte7 = r12 & 0xFF
    
    return byte3, byte7
