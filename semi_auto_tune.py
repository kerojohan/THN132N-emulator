#!/usr/bin/env python3
"""
Semi-automatic RF tuning script.
Modifies values, asks user to upload manually, then measures with rtl_433.
"""
import re
import subprocess
import time
import sys

INO_FILE = "attiny/attiny85THN132N_aht20.ino"
RTL_433_CMD = ["rtl_433", "-A", "-T", "60"]

# Tuning parameters
TARGET_HIGH = 492
TARGET_LOW = 476
TARGET_GAP = 8784

# Limits
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
        r"(const\s+uint16_t\s+HIGH_UNIT_US\s*=\s*)(\d+);",
        f"\\g<1>{new_high};",
        content,
    )
    content = re.sub(
        r"(const\s+uint16_t\s+LOW_UNIT_US\s*=\s*)(\d+);",
        f"\\g<1>{new_low};",
        content,
    )
    content = re.sub(
        r"(const\s+uint16_t\s+INTER_FRAME_GAP_US\s*=\s*)(\d+);",
        f"\\g<1>{new_gap};",
        content,
    )

    with open(filename, "w") as f:
        f.write(content)
    print(f"✓ Updated firmware: High={new_high}, Low={new_low}, Gap={new_gap}")


def measure_rf():
    print("\n⏱  Listening with rtl_433 (60s)...")
    try:
        result = subprocess.run(RTL_433_CMD, capture_output=True, text=True, timeout=65)
        return result.stdout
    except subprocess.TimeoutExpired:
        print("⚠  Measurement timed out.")
        return ""
    except Exception as e:
        print(f"✗ rtl_433 failed: {e}")
        return ""


def parse_analysis(output):
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
            m = re.search(r"width:\s+(\d+)\s+us.*\[(\d+);(\d+)\]", line)
            if m:
                w = int(m.group(1))
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
    print("=" * 60)
    print("  Semi-Automatic RF Tuning Script")
    print("=" * 60)

    for iteration in range(10):  # Max 10 iterations
        print(f"\n{'─' * 60}")
        print(f"  Iteration {iteration + 1}")
        print(f"{'─' * 60}")

        # 1. Read current
        curr_h, curr_l, curr_g = read_current_values(INO_FILE)
        print(f"\n📋 Current Config: High={curr_h}, Low={curr_l}, Gap={curr_g}")

        # 2. Wait for manual upload
        print("\n🔧 MANUAL STEP:")
        print(f"   1. Open Arduino IDE")
        print(f"   2. Upload {INO_FILE}")
        print(f"   3. Unplug/replug Digispark when prompted")
        input("\n   Press ENTER when upload is complete...")

        # 3. Measure
        output = measure_rf()
        if not output:
            print("✗ No data received.")
            break

        meas_h, meas_l, meas_g = parse_analysis(output)
        print(f"\n📊 Measured: High={meas_h}, Low={meas_l}, Gap={meas_g}")

        if meas_h is None or meas_l is None:
            print("✗ Could not parse Pulse/Gap widths. Signal too weak?")
            break

        # 4. Calculate error
        err_h = TARGET_HIGH - meas_h
        err_l = TARGET_LOW - meas_l
        err_g = TARGET_GAP - meas_g if meas_g else 0

        print(f"📉 Errors: High={err_h:+d}, Low={err_l:+d}, Gap={err_g:+d}")

        # 5. Convergence check
        if abs(err_h) <= 4 and abs(err_l) <= 4:
            print("\n✅ CONVERGED within tolerance!")
            print(f"Final values: High={curr_h}, Low={curr_l}, Gap={curr_g}")
            break

        # 6. Adjust
        adj_h = int(err_h * 0.5)
        adj_l = int(err_l * 0.5)
        adj_g = int(err_g * 0.8)

        # Prevent stagnation
        if err_h != 0 and adj_h == 0:
            adj_h = 1 if err_h > 0 else -1
        if err_l != 0 and adj_l == 0:
            adj_l = 1 if err_l > 0 else -1

        new_h = max(MIN_VAL, min(MAX_VAL, curr_h + adj_h))
        new_l = max(MIN_VAL, min(MAX_VAL, curr_l + adj_l))
        new_g = curr_g + adj_g if meas_g else curr_g

        print(
            f"\n🔄 Next iteration: High {curr_h}→{new_h}, Low {curr_l}→{new_l}, Gap {curr_g}→{new_g}"
        )

        update_values(INO_FILE, new_h, new_l, new_g)
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠  Interrupted by user.")
        sys.exit(0)
