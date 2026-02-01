#!/usr/bin/env python3
from r12_lut import R12_LUT

def get_r12_for_temp(temp_c):
    key = f"{round(float(temp_c), 1):.1f}"
    if key not in R12_LUT:
        raise ValueError(f"No tengo R12 para temperatura {key} °C")
    r12_hex = R12_LUT[key]   # ej. "0x2F6"
    r12_int = int(r12_hex, 16)
    b3_low = (r12_int >> 8) & 0xF
    b7     = r12_int & 0xFF
    return r12_hex, b3_low, b7

if __name__ == "__main__":
    for t in sorted(R12_LUT.keys())[:5]:
        r12_hex, b3_low, b7 = get_r12_for_temp(t)
        print(f"{t} °C -> {r12_hex}  (b3_low=0x{b3_low:X}, b7=0x{b7:02X})")
