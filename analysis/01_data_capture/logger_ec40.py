#!/usr/bin/env python3
import subprocess
import csv
import time
import re

CSV_FILE = "ec40_live.csv"

CSV_HEADER = [
    "timestamp",
    "model",
    "raw168",
    "raw64",
    "temp",
    "channel",
    "house_code",
    "battery",
    "sensor_type_hex",
    "rolling_code_hex",
    "checksum_hex"
]

# Regex
re_model  = re.compile(r"model\s*:\s*([A-Za-z0-9\-\_]+)")
re_raw168 = re.compile(r"codes\s+:\s+\{168\}([0-9a-fA-F]+)")
re_raw64  = re.compile(r"codes\s+:\s+\{64\}([0-9a-fA-F]+)")
re_temp   = re.compile(r"Celsius\s+:\s+([-0-9.]+)")
re_ch     = re.compile(r"Channel\s+:\s+(\d+)")
re_house  = re.compile(r"House Code:\s+(\d+)")
re_batt   = re.compile(r"Battery\s+:\s+(\d+)")

seen = set()

def ensure_csv():
    try:
        with open(CSV_FILE, "x", newline="") as f:
            csv.writer(f).writerow(CSV_HEADER)
    except FileExistsError:
        pass

def decode_ec40_fields(raw64):
    """
    Decodifica los campos EC40:
    - raw64: string hex de 16 chars (8 bytes).
    """
    bytes_arr = bytes.fromhex(raw64)

    # Byte 0 nibble alto = type (0x8 en THN132N)
    sensor_type = (bytes_arr[0] >> 4) & 0x0F

    # Byte 1 = rolling code
    rolling_code = bytes_arr[1]

    # Bytes 6+7 (12 bits) = checksum
    checksum = (bytes_arr[6] << 4) | (bytes_arr[7] >> 4)

    return sensor_type, rolling_code, checksum


def parse_block(block):
    model = re_model.search(block)
    raw168 = re_raw168.search(block)
    raw64  = re_raw64.search(block)
    temp   = re_temp.search(block)
    ch     = re_ch.search(block)
    house  = re_house.search(block)
    batt   = re_batt.search(block)

    if not model or not raw168 or not raw64 or not temp:
        return None

    model = model.group(1)
    raw168 = raw168.group(1)
    raw64 = raw64.group(1)

    # decodificación EC40
    stype, roll, chk = decode_ec40_fields(raw64)

    return {
        "model": model,
        "raw168": raw168,
        "raw64": raw64,
        "temp": float(temp.group(1)),
        "channel": int(ch.group(1)) if ch else None,
        "house_code": int(house.group(1)) if house else None,
        "battery": int(batt.group(1)) if batt else None,
        "sensor_type_hex": f"0x{stype:X}",
        "rolling_code_hex": f"0x{roll:X}",
        "checksum_hex": f"0x{chk:X}"
    }


def main():
    ensure_csv()

    print("Escuchando rtl_433… (Ctrl+C para salir)\n")

    p = subprocess.Popen(
        ["rtl_433", "-R", "12"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    block = ""
    try:
        for line in p.stdout:
            block += line

            # Fin de bloque
            if line.strip() == "" or line.startswith("_ _"):
                data = parse_block(block)

                if data:
                    key = data["raw168"]

                    if key not in seen:
                        seen.add(key)

                        with open(CSV_FILE, "a", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                time.strftime("%Y-%m-%d %H:%M:%S"),
                                data["model"],
                                data["raw168"],
                                data["raw64"],
                                data["temp"],
                                data["channel"],
                                data["house_code"],
                                data["battery"],
                                data["sensor_type_hex"],
                                data["rolling_code_hex"],
                                data["checksum_hex"],
                            ])

                        print(f"[new] {data['model']}  {data['temp']}°C "
                              f"EC40={data['raw64']} "
                              f"type={data['sensor_type_hex']} roll={data['rolling_code_hex']} chk={data['checksum_hex']}")

                block = ""

    except KeyboardInterrupt:
        print("\nSaliendo…")
        p.kill()


if __name__ == "__main__":
    main()
