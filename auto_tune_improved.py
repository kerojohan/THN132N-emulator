#!/usr/bin/env python3
"""
Improved auto-tuning script with better timing for manual Digispark reset.
"""
import re
import subprocess
import time
import sys
import os

INO_FILE = "attiny/attiny85THN132N_aht20.ino"
RTL_433_CMD = ["rtl_433", "-R", "12", "-A", "-vvv", "-T", "60"]

# Tuning parameters (Based on USER'S ORIGINAL SENSOR - Channel 1)
TARGET_HIGH = 512
TARGET_LOW = 456
TARGET_GAP = 9248

# Limits
MIN_VAL = 200
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


def flash_firmware():
    print("\n" + "=" * 60)
    print("  PREPARING TO FLASH FIRMWARE")
    print("=" * 60)

    # Create temporary sketch structure
    temp_sketch_dir = "attiny85THN132N_aht20"
    temp_ino_file = f"{temp_sketch_dir}/{temp_sketch_dir}.ino"

    try:
        # Clean up any previous temp directory
        if os.path.exists(temp_sketch_dir):
            import shutil

            shutil.rmtree(temp_sketch_dir)

        # Create temp directory and symlink
        os.makedirs(temp_sketch_dir, exist_ok=True)
        os.symlink(os.path.abspath("attiny/attiny85THN132N_aht20.ino"), temp_ino_file)

        # First, compile only (no upload yet)
        print("\n⚙️  Compiling sketch...")
        compile_cmd = [
            "/home/joan/Projectes/OregonDecoding/Antigravity/bin/arduino-cli",
            "compile",
            "-b",
            "ATTinyCore:avr:attinyx5micr",
            temp_sketch_dir,
        ]

        result = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"❌ Compilation failed: {result.stderr}")
            return False

        print("✓ Compilation successful!")

        # Now give user time to prepare for upload
        print("\n" + "🔴" * 20)
        print("\n  ⚠️  GET READY TO UNPLUG/REPLUG DIGISPARK!")
        print("\n" + "🔴" * 20)

        for i in range(5, 0, -1):
            print(f"\n  Starting upload in {i} seconds...", end="", flush=True)
            time.sleep(1)

        print("\n\n🚀 Starting upload NOW!")
        print("   👉 UNPLUG and REPLUG the Digispark within the next 10 seconds!\n")

        # Now upload
        upload_cmd = [
            "/home/joan/Projectes/OregonDecoding/Antigravity/bin/arduino-cli",
            "upload",
            "-b",
            "ATTinyCore:avr:attinyx5micr",
            "-p",
            "/dev/ttyACM0",  # Dummy port, micronucleus doesn't use it
            temp_sketch_dir,
        ]

        result = subprocess.run(upload_cmd, capture_output=True, text=True, timeout=90)

        # Check output
        output = result.stdout + result.stderr
        if "done. Thank you!" in output or "successfully" in output.lower():
            print("\n✅ Upload successful!")
            return True
        elif "Aborted" in output or "Timeout" in output:
            print("\n❌ Upload FAILED - Device not detected")
            print("   Did you unplug/replug in time?")
            return False
        else:
            print("\n⚠️  Upload status unclear")
            print(output[-300:])
            # If no clear error, assume success
            return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(temp_sketch_dir):
            import shutil

            shutil.rmtree(temp_sketch_dir)


def measure_rf():
    print("\n⏱  Listening with rtl_433 (60s)...")
    try:
        # Merge stderr into stdout to capture everything
        result = subprocess.run(
            RTL_433_CMD,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=65,
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        print("⚠  Measurement timed out.")
        return ""
    except Exception as e:
        print(f"✗ rtl_433 failed: {e}")
        return ""


def parse_analysis(output):
    lines = output.split("\n")

    # 1. VERIFY Correct Sensor & Print Details
    if "Oregon-THN132N" not in output:
        print("\n⚠️  WARNING: 'Oregon-THN132N' not detected in output!")

    print("\n🔎 Detected Sensor Frame(s):")
    print("-" * 40)
    found_details = False
    for i, line in enumerate(lines):
        if "Oregon-THN132N" in line:
            # Print surrounding lines to show context (Time, Model, Channel)
            start = max(0, i - 1)
            end = min(len(lines), i + 4)  # Capture a bit more context (Battery, etc.)
            for j in range(start, end):
                if j < len(lines) and lines[j].strip():
                    print(f"   {lines[j]}")
            print("   ---")  # Separator between multiple detections
            found_details = True

    if not found_details:
        print("   (No 'model :' lines found in output)")
    print("-" * 40)

    # Store candidates as (count, width)
    pulse_candidates = []
    gap_candidates = []
    frame_gap_candidates = []

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

        # Regex to capture count and width: "[ 0] count:  140,  width: 1012 us"
        m = re.search(r"count:\s+(\d+),\s+width:\s+(\d+)\s+us", line)
        if m:
            count = int(m.group(1))
            width = int(m.group(2))

            if in_pulse_section:
                # Target Short Pulse (~512us). Range 300-600.
                if 300 < width < 700:
                    # Filter out noise with very low counts (e.g. < 5)
                    if count > 5:
                        pulse_candidates.append((count, width))

            if in_gap_section:
                # Target Short Gap (~428us). Range 300-600.
                if 300 < width < 700:
                    if count > 5:
                        gap_candidates.append((count, width))
                # Target Frame Gap (~8K-9K). Range > 6000.
                elif width > 6000:
                    frame_gap_candidates.append((count, width))

    # Select best candidates based on highest count (most frequent)
    # Sort by count descending
    pulse_candidates.sort(key=lambda x: x[0], reverse=True)
    gap_candidates.sort(key=lambda x: x[0], reverse=True)
    frame_gap_candidates.sort(key=lambda x: x[0], reverse=True)

    pulse_width = pulse_candidates[0][1] if pulse_candidates else None
    gap_width = gap_candidates[0][1] if gap_candidates else None
    frame_gap = frame_gap_candidates[0][1] if frame_gap_candidates else None

    # Debug info
    if pulse_candidates:
        print(f"   🔎 Best Pulse: {pulse_width}us (count={pulse_candidates[0][0]})")
    if gap_candidates:
        print(f"   🔎 Best Gap: {gap_width}us (count={gap_candidates[0][0]})")
    if frame_gap_candidates:
        print(
            f"   🔎 Best Frame Gap: {frame_gap}us (count={frame_gap_candidates[0][0]})"
        )

    return pulse_width, gap_width, frame_gap


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--steps", type=int, default=1, help="Number of tuning iterations"
    )
    args = parser.parse_args()

    for i in range(args.steps):
        # 2. Flash
        if not flash_firmware():
            print("\n❌ Flash failed, stopping.")
            break

    print("\n\n🏁 Auto-tuning finished!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠  Interrupted by user.")
        sys.exit(0)
