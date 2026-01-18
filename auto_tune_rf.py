#!/usr/bin/env python3
import re
import subprocess
import time
import sys
import shutil
import argparse

# --- CONFIGURATION ---
INO_FILE = "attiny/attiny85THN132N_aht20.ino"
RTL_433_CMD = [
    "rtl_433",
    "-A",
    "-T",
    "60",
    "-R",
    "0",
]  # -R 0 disabling decoders might be safer to see raw pulses? No, we need analysis.
# We'll use -A for the pulse analyzer.
# ATTinyCore FQBN for Digispark ATtiny85 with Micronucleus bootloader
# Micronucleus doesn't use a serial port - upload happens via USB HID
# We need to use absolute path because there are multiple .ino files in attiny/
import os

SKETCH_PATH = os.path.abspath("attiny/attiny85THN132N_aht20.ino")
FLASH_CMD = [
    "arduino-cli",
    "compile",
    "--upload",
    "-b",
    "ATTinyCore:avr:attinyx5micr:chip=85,clock=16internal,eesave=aenable,bod=disable,millis=enabled",
    SKETCH_PATH,
]

# Tuning parameters
TARGET_HIGH = 492
TARGET_LOW = 476
TARGET_GAP = 8784

# Limits to prevent bricking/nonsense
MIN_VAL = 400
MAX_VAL = 600


def read_current_values(filename):
    with open(filename, "r") as f:
        content = f.read()

    high_match = re.search(r"const\s+uint16_t\s+HIGH_UNIT_US\s*=\s*(\d+);", content)
    low_match = re.search(r"const\s+uint16_t\s+LOW_UNIT_US\s*=\s*(\d+);", content)
    gap_match = re.search(
        r"const\s+uint16_t\s+INTER_FRAME_GAP_US\s*=\s*(\d+);", content
    )

    if not (high_match and low_match and gap_match):
        print("Error: Could not find constants in .ino file")
        sys.exit(1)

    return int(high_match.group(1)), int(low_match.group(1)), int(gap_match.group(1))


def update_values(filename, new_high, new_low, new_gap):
    with open(filename, "r") as f:
        content = f.read()

    content = re.sub(
        r"(const\s+uint16_t\s+HIGH_UNIT_US\s*=\s*)(\d+);", f"\\g<1>{new_high};", content
    )
    content = re.sub(
        r"(const\s+uint16_t\s+LOW_UNIT_US\s*=\s*)(\d+);", f"\\g<1>{new_low};", content
    )
    content = re.sub(
        r"(const\s+uint16_t\s+INTER_FRAME_GAP_US\s*=\s*)(\d+);",
        f"\\g<1>{new_gap};",
        content,
    )

    with open(filename, "w") as f:
        f.write(content)
    print(f"Updated firmware: High={new_high}, Low={new_low}, Gap={new_gap}")


def flash_firmware():
    print("\n🔄 Resetting USB to trigger bootloader...")

    # Reset USB with sudo (only this part needs sudo)
    try:
        result = subprocess.run(
            ["sudo", "python3", "usb_reset.py"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            print("✓ USB reset successful")
            time.sleep(2)  # Give device time to enter bootloader
        else:
            print(f"⚠ USB reset failed: {result.stderr}")
            print("Continuing anyway...")
    except Exception as e:
        print(f"⚠ USB reset error: {e}")

    # Arduino-cli requires sketch folder name to match .ino filename
    # Create a temporary proper structure
    temp_sketch_dir = "attiny85THN132N_aht20"
    temp_ino_file = f"{temp_sketch_dir}/{temp_sketch_dir}.ino"

    try:
        # Clean up any previous temp directory
        if os.path.exists(temp_sketch_dir):
            import shutil

            shutil.rmtree(temp_sketch_dir)

        # Create temp directory and symlink the .ino file
        os.makedirs(temp_sketch_dir, exist_ok=True)
        os.symlink(os.path.abspath("attiny/attiny85THN132N_aht20.ino"), temp_ino_file)

        # Update FLASH_CMD to use the temp sketch
        # Simplified FQBN - the chip options aren't supported in this format
        # Use local arduino-cli installation (not snap)
        flash_cmd = [
            "/home/joan/Projectes/OregonDecoding/Antigravity/bin/arduino-cli",
            "compile",
            "--upload",
            "-b",
            "ATTinyCore:avr:attinyx5micr",
            temp_sketch_dir,
        ]

        print(f"Flashing firmware... Command: {' '.join(flash_cmd)}")
        subprocess.run(flash_cmd, check=True, timeout=60)
        print("Flash successful.")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Flash failed: {e}")
        return False
    except subprocess.TimeoutExpired:
        print("Flash timed out. Did you replug the device?")
        return False
    finally:
        # Clean up temp directory
        if os.path.exists(temp_sketch_dir):
            import shutil

            shutil.rmtree(temp_sketch_dir)


def measure_rf():
    print("Listening with rtl_433 (60s timeout)...")
    try:
        # Capture stderr/stdout. rtl_433 prints analysis to stdout usually.
        result = subprocess.run(RTL_433_CMD, capture_output=True, text=True, timeout=65)
        return result.stdout
    except subprocess.TimeoutExpired:
        print("Measurement timed out.")
        return ""
    except Exception as e:
        print(f"rtl_433 failed: {e}")
        return ""


def parse_analysis(output):
    # Looking for:
    # [ 0] count:  132,  width: 1008 us ...
    # [ 1] count:   72,  width:  500 us ...
    # We want the "Short" pulse (count ~64-72, width ~500)

    lines = output.split("\n")
    pulse_width = None
    gap_width = None
    frame_gap = None

    in_pulse_section = False
    in_gap_section = False

    for line in lines:
        if "Pulse width distribution" in line:
            in_pulse_section = True
            in_gap_section = False
            continue
        if "Gap width distribution" in line:
            in_pulse_section = False
            in_gap_section = True
            continue

        if in_pulse_section:
            # Match: [ 1] count:   72,  width:  500 us
            m = re.search(r"width:\s+(\d+)\s+us.*\[(\d+);(\d+)\]", line)
            if m:
                w = int(m.group(1))
                # Heuristic: Short pulse is around 400-600. Long is ~1000.
                if 300 < w < 700:
                    pulse_width = w

        if in_gap_section:
            m = re.search(r"width:\s+(\d+)\s+us.*\[(\d+);(\d+)\]", line)
            if m:
                w = int(m.group(1))
                if 300 < w < 700:
                    gap_width = w
                elif w > 7000:
                    frame_gap = w

    return pulse_width, gap_width, frame_gap


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--steps", type=int, default=1, help="Number of tuning iterations"
    )
    parser.add_argument("--port", type=str, help="Serial port for upload")
    args = parser.parse_args()

    if args.port:
        # Update the FLASH_CMD dynamically
        for i, arg in enumerate(FLASH_CMD):
            if arg == "/dev/ttyUSB0":
                FLASH_CMD[i] = args.port

    for i in range(args.steps):
        print(f"\n--- Iteration {i+1}/{args.steps} ---")

        # 1. Read current
        curr_h, curr_l, curr_g = read_current_values(INO_FILE)
        print(f"Current Config: High={curr_h}, Low={curr_l}, Gap={curr_g}")

        # 2. Flash (Assuming code is already set for measurement, or we just measure first?)
        # Let's assume we modify THEN flash. For first run, just flash what's there?
        # Better: Flash current, Measure, then Calculate next.

        if not flash_firmware():
            break

        # 3. Measure
        output = measure_rf()
        if not output:
            print("No data received.")
            break

        meas_h, meas_l, meas_g = parse_analysis(output)
        print(f"Measured: High={meas_h}, Low={meas_l}, Gap={meas_g}")

        if meas_h is None or meas_l is None:
            print("Could not parse Pulse/Gap widths. Signal too weak or garbage?")
            break

        # 4. Calculate error
        err_h = TARGET_HIGH - meas_h
        err_l = TARGET_LOW - meas_l
        err_g = TARGET_GAP - meas_g if meas_g else 0

        print(f"Errors: High={err_h}, Low={err_l}, Gap={err_g}")

        # 5. Convergence check
        if abs(err_h) <= 4 and abs(err_l) <= 4:
            print("CONVERGED within tolerance!")
            break

        # 6. Adjust
        # Simple proportional control with limit
        # If measured is 500 and target is 492 (Err -8). We need to lower Config.
        # But Config 508 gave 500. So we need Config 500?
        # Assume 1:1 relation approx.

        # Damping factor 0.5 to avoid oscillation
        adj_h = int(err_h * 0.5)
        adj_l = int(err_l * 0.5)
        adj_g = int(err_g * 0.8)  # Gap is usually linear

        # Prevent stagnation (if error exists but 0.5 makes it 0)
        if err_h != 0 and adj_h == 0:
            adj_h = 1 if err_h > 0 else -1
        if err_l != 0 and adj_l == 0:
            adj_l = 1 if err_l > 0 else -1

        new_h = curr_h + adj_h
        new_l = curr_l + adj_l
        new_g = curr_g + adj_g if meas_g else curr_g

        # Safety clamps
        new_h = max(MIN_VAL, min(MAX_VAL, new_h))
        new_l = max(MIN_VAL, min(MAX_VAL, new_l))

        print(
            f"Adjusting: High {curr_h}->{new_h}, Low {curr_l}->{new_l}, Gap {curr_g}->{new_g}"
        )

        update_values(INO_FILE, new_h, new_l, new_g)

        # Ready for next loop (Flash -> Measure)
        time.sleep(2)


if __name__ == "__main__":
    main()
