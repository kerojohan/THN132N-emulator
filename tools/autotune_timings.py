#!/usr/bin/env python3
import argparse
import datetime as dt
import os
import re
import subprocess
import sys
import time

MODEL_RE = re.compile(r"model\s*:\s*(?:Oregon-)?THN132N", re.IGNORECASE)
DIST_LINE_RE = re.compile(r"\[\s*\d+\]\s+count:\s+(\d+),\s+width:\s+(\d+)\s+us")
DEMOD_RE = re.compile(r"reset_limit:\s*(\d+)")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
TOTAL_RE = re.compile(r"Total count:\s*(\d+)")


def run_cmd(cmd, timeout_s=None):
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        out, _ = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate()
    return proc.returncode, out or ""


def strip_ansi(line):
    return ANSI_RE.sub("", line)


def resolve_sketch_paths(sketch_arg):
    if os.path.isdir(sketch_arg):
        base = os.path.basename(os.path.normpath(sketch_arg))
        preferred = os.path.join(sketch_arg, base + ".ino")
        if os.path.exists(preferred):
            return sketch_arg, preferred
        ino_files = [f for f in os.listdir(sketch_arg) if f.endswith(".ino")]
        if len(ino_files) == 1:
            return sketch_arg, os.path.join(sketch_arg, ino_files[0])
        raise RuntimeError("No se pudo determinar el .ino principal en el directorio del sketch.")
    if not os.path.exists(sketch_arg):
        raise RuntimeError("No existe el sketch indicado.")
    sketch_dir = os.path.dirname(sketch_arg) or "."
    return sketch_dir, sketch_arg


def power_cycle_usb(args):
    if not args.power_cycle:
        return True
    if not args.uhubctl_hub or not args.uhubctl_port:
        print("Falta --uhubctl-hub o --uhubctl-port para power cycle.")
        return False
    off_cmd = f"{args.uhubctl_bin} -l {args.uhubctl_hub} -p {args.uhubctl_port} -a 0"
    on_cmd = f"{args.uhubctl_bin} -l {args.uhubctl_hub} -p {args.uhubctl_port} -a 1"
    print("Cortando alimentacion USB...")
    code, out = run_cmd(off_cmd)
    print(out)
    if code != 0:
        return False
    time.sleep(args.power_cycle_delay)
    print("Restaurando alimentacion USB...")
    code, out = run_cmd(on_cmd)
    print(out)
    if code != 0:
        return False
    time.sleep(args.boot_wait)
    return True


def prepare_for_upload(args):
    if args.power_cycle:
        return power_cycle_usb(args)
    print("Desconecta el Digispark y vuelve a conectarlo cuando el uploader lo pida.")
    print("Pulsa Enter para iniciar el upload.")
    input()
    return True


def parse_distribution(lines, start_idx):
    entries = []
    i = start_idx + 1
    while i < len(lines):
        m = DIST_LINE_RE.search(lines[i])
        if not m:
            break
        count = int(m.group(1))
        width = int(m.group(2))
        entries.append((count, width))
        i += 1
    return entries


def find_pulse_block(lines, require_model=True):
    model_idxs = [i for i, line in enumerate(lines) if MODEL_RE.search(line)]
    pulse_idxs = [i for i, line in enumerate(lines) if "Pulse width distribution:" in line]
    if not pulse_idxs:
        return None
    if not require_model:
        return pulse_idxs[-1]
    if not model_idxs:
        return None
    candidates = []
    for pidx in pulse_idxs:
        prev_models = [i for i in model_idxs if i < pidx]
        if not prev_models:
            continue
        last_model_idx = prev_models[-1]
        if MODEL_RE.search(lines[last_model_idx]):
            candidates.append(pidx)
    return candidates[-1] if candidates else None


def collect_blocks(lines):
    blocks = []
    total_count = None
    last_model_idx = None
    for i, line in enumerate(lines):
        if MODEL_RE.search(line):
            last_model_idx = i
        if "Detected OOK package" in line:
            total_count = None
        m = TOTAL_RE.search(line)
        if m:
            total_count = int(m.group(1))
        if "Pulse width distribution:" not in line:
            continue
        pulse_entries = parse_distribution(lines, i)
        gap_idx = next((j for j in range(i + 1, len(lines)) if "Gap width distribution:" in lines[j]), None)
        if gap_idx is None:
            continue
        gap_entries = parse_distribution(lines, gap_idx)
        timing_entries = []
        for j in range(gap_idx + 1, min(len(lines), gap_idx + 60)):
            if "Detected OOK package" in lines[j] or "Pulse width distribution:" in lines[j]:
                break
            if "Timing distribution:" in lines[j]:
                timing_entries = parse_distribution(lines, j)
                break
        window_start = max(0, i - 80)
        window_end = min(len(lines), i + 80)
        model_match = any(MODEL_RE.search(lines[j]) for j in range(window_start, window_end))
        blocks.append(
            {
                "pulse_entries": pulse_entries,
                "gap_entries": gap_entries,
                "timing_entries": timing_entries,
                "total_count": total_count,
                "model_match": model_match,
                "model_distance": i - last_model_idx if last_model_idx is not None else None,
                "pulse_total": sum(c for c, _ in pulse_entries),
            }
        )
    return blocks


def select_widths(entries, min_count):
    filtered = [w for c, w in entries if c >= min_count]
    if filtered:
        return sorted(filtered)
    top = sorted(entries, key=lambda x: x[0], reverse=True)[:2]
    return sorted([w for _, w in top]) if top else []


def extract_metrics(
    output,
    min_count,
    require_model=True,
    min_pulse_total=0,
    min_total_count=0,
    model_window=20,
    min_long_gap=2000,
):
    lines = [strip_ansi(line) for line in output.splitlines()]
    blocks = collect_blocks(lines)
    if not blocks:
        return None
    if require_model:
        candidates = [
            b
            for b in blocks
            if b["model_distance"] is not None and b["model_distance"] <= model_window
        ]
        if not candidates:
            return None
    else:
        candidates = blocks
    if min_pulse_total > 0:
        candidates = [b for b in candidates if b["pulse_total"] >= min_pulse_total]
    if min_total_count > 0:
        candidates = [
            b
            for b in candidates
            if b["total_count"] is not None and b["total_count"] >= min_total_count
        ]
    if not candidates:
        return None
    candidates = sorted(
        candidates,
        key=lambda b: (b["total_count"] or 0, b["pulse_total"]),
        reverse=True,
    )
    block = candidates[0]

    pulse_entries = block["pulse_entries"]
    gap_entries = block["gap_entries"]
    timing_entries = block["timing_entries"]
    pulse_widths = select_widths(pulse_entries, min_count)
    gap_widths = select_widths(gap_entries, min_count)
    if not pulse_widths or not gap_widths:
        return None

    short_high = min(pulse_widths)
    short_low = min(gap_widths)
    long_gap = None
    if timing_entries:
        long_gap = max(w for _, w in timing_entries)
    if gap_entries:
        gap_max = max(w for _, w in gap_entries)
        if long_gap is None or gap_max > long_gap:
            long_gap = gap_max
    if long_gap is not None and long_gap < min_long_gap:
        long_gap = None

    reset_limit = None
    for line in lines:
        m = DEMOD_RE.search(line)
        if m:
            reset_limit = int(m.group(1))
    return {
        "short_high": short_high,
        "short_low": short_low,
        "long_gap": long_gap,
        "reset_limit": reset_limit,
    }


def read_timings(sketch_path):
    text = open(sketch_path, "r", encoding="utf-8", errors="replace").read()
    hi = re.search(r"HIGH_UNIT_US\s*=\s*(\d+)", text)
    lo = re.search(r"LOW_UNIT_US\s*=\s*(\d+)", text)
    gap = re.search(r"INTER_FRAME_GAP_US\s*=\s*(\d+)", text)
    if not (hi and lo and gap):
        raise RuntimeError("No se pudieron leer los timings del sketch.")
    return int(hi.group(1)), int(lo.group(1)), int(gap.group(1))


def write_timings(sketch_path, hi, lo, gap):
    text = open(sketch_path, "r", encoding="utf-8", errors="replace").read()
    text = re.sub(r"(HIGH_UNIT_US\s*=\s*)\d+", r"\g<1>%d" % hi, text, count=1)
    text = re.sub(r"(LOW_UNIT_US\s*=\s*)\d+", r"\g<1>%d" % lo, text, count=1)
    text = re.sub(r"(INTER_FRAME_GAP_US\s*=\s*)\d+", r"\g<1>%d" % gap, text, count=1)
    with open(sketch_path, "w", encoding="utf-8") as f:
        f.write(text)


def clamp(val, vmin, vmax):
    return max(vmin, min(vmax, val))


def adjust(current, measured, target, gain, max_step, vmin, vmax):
    delta = target - measured
    step = int(round(gain * delta))
    step = clamp(step, -max_step, max_step)
    return clamp(current + step, vmin, vmax)


def read_last_log_values(log_path):
    if not os.path.exists(log_path):
        return None
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        lines = [line.strip() for line in f if line.strip()]
    if len(lines) < 2:
        return None
    for line in reversed(lines):
        if line.lower().startswith("ts,"):
            continue
        parts = line.split(",")
        if len(parts) < 8:
            continue
        try:
            hi = int(parts[5])
            lo = int(parts[6])
            gap = int(parts[7])
            return hi, lo, gap
        except ValueError:
            continue
    return None


def main():
    ap = argparse.ArgumentParser(description="Autotune timings for Oregon THN132N (rtl_433 + arduino-cli).")
    ap.add_argument("--sketch", default="firmware/attiny/attiny85THN132N_aht20.ino")
    ap.add_argument("--rtl-cmd", default="rtl_433 -R 12 -A -vvv")
    ap.add_argument("--capture-seconds", type=int, default=60)
    ap.add_argument("--max-iterations", type=int, default=0)
    ap.add_argument("--min-count", type=int, default=10)
    ap.add_argument("--min-pulse-total", type=int, default=50)
    ap.add_argument("--min-total-count", type=int, default=50)
    ap.add_argument("--model-window", type=int, default=20)
    ap.add_argument("--min-long-gap", type=int, default=2000)
    ap.add_argument("--target-high", type=int, default=512)
    ap.add_argument("--target-low", type=int, default=456)
    ap.add_argument("--target-gap", type=int, default=9248)
    ap.add_argument("--tolerance-high", type=int, default=6)
    ap.add_argument("--tolerance-low", type=int, default=6)
    ap.add_argument("--tolerance-gap", type=int, default=120)
    ap.add_argument("--stable-iterations", type=int, default=2)
    ap.add_argument("--gain", type=float, default=0.6)
    ap.add_argument("--gap-gain", type=float, default=0.6)
    ap.add_argument("--max-step", type=int, default=40)
    ap.add_argument("--gap-max-step", type=int, default=600)
    ap.add_argument("--fallback-high", type=int, default=512)
    ap.add_argument("--fallback-low", type=int, default=456)
    ap.add_argument("--fallback-gap", type=int, default=9248)
    ap.add_argument("--max-missed", type=int, default=1)
    ap.add_argument("--continue-on-miss", action="store_true")
    ap.add_argument("--reupload-last-good", action="store_true")
    ap.add_argument("--miss-reupload-threshold", type=int, default=1)
    ap.add_argument("--post-upload-wait", type=float, default=2.0)
    ap.add_argument("--no-model-filter", action="store_true")
    ap.add_argument("--parse-only", action="store_true")
    ap.add_argument("--input-file", default="")
    ap.add_argument("--dump-on-miss", default="")
    ap.add_argument("--fqbn", default=os.environ.get("ARDUINO_FQBN", "digistump:avr:digispark-tiny"))
    ap.add_argument("--port", default=os.environ.get("ARDUINO_PORT", ""))
    ap.add_argument("--arduino-cli", default=os.environ.get("ARDUINO_CLI", "arduino-cli"))
    ap.add_argument("--log-path", default="logs/tuning_log.csv")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--manual-upload", action="store_true")
    ap.add_argument("--power-cycle", action="store_true")
    ap.add_argument("--uhubctl-bin", default="uhubctl")
    ap.add_argument("--uhubctl-hub", default="")
    ap.add_argument("--uhubctl-port", default="")
    ap.add_argument("--power-cycle-delay", type=float, default=1.0)
    ap.add_argument("--boot-wait", type=float, default=1.0)
    args = ap.parse_args()

    if args.parse_only:
        if args.input_file:
            with open(args.input_file, "r", encoding="utf-8", errors="replace") as f:
                input_text = f.read()
        else:
            input_text = sys.stdin.read()
        metrics = extract_metrics(
            input_text,
            args.min_count,
            require_model=not args.no_model_filter,
            min_pulse_total=args.min_pulse_total,
            min_total_count=args.min_total_count,
            model_window=args.model_window,
            min_long_gap=args.min_long_gap,
        )
        if not metrics:
            print("No se pudieron extraer métricas.")
            return 2
        print(
            "Medido short_high={short_high} short_low={short_low} long_gap={long_gap} reset_limit={reset_limit}".format(
                **metrics
            )
        )
        return 0

    if not args.fqbn and not args.manual_upload:
        print("Falta FQBN. Exporta ARDUINO_FQBN o pasa --fqbn.")
        print("Ejemplo Digispark: digistump:avr:digispark-tiny")
        return 2
    if args.power_cycle and args.manual_upload:
        print("No tiene sentido --power-cycle con --manual-upload.")
        return 2

    log_path = args.log_path
    if not os.path.exists(log_path):
        with open(log_path, "w", encoding="ascii") as f:
            f.write("ts,short_high,short_low,long_gap,reset_limit,hi,lo,gap\n")

    missed = 0
    stable = 0
    last_good = None
    sketch_dir, sketch_file = resolve_sketch_paths(args.sketch)

    last_logged = read_last_log_values(log_path)
    if last_logged:
        last_good = last_logged

    if args.resume:
        if last_logged:
            resume_hi, resume_lo, resume_gap = last_logged
            write_timings(sketch_file, resume_hi, resume_lo, resume_gap)
            print(f"Resume: hi={resume_hi} lo={resume_lo} gap={resume_gap}")
        else:
            print("Resume solicitado, pero no hay datos en el log. Usando timings del sketch.")

    it = 0
    while True:
        it += 1
        if args.max_iterations > 0 and it > args.max_iterations:
            print("Se alcanzo el maximo de iteraciones sin converger.")
            return 1
        hi, lo, gap = read_timings(sketch_file)
        print(f"\nIter {it}: current hi={hi} lo={lo} gap={gap}")

        print(f"Capturando rtl_433 durante {args.capture_seconds}s...")
        start_ts = time.time()
        code, output = run_cmd(args.rtl_cmd, timeout_s=args.capture_seconds)
        elapsed = time.time() - start_ts
        if elapsed < max(2.0, args.capture_seconds * 0.5):
            wait_more = max(0.0, args.capture_seconds - elapsed)
            if wait_more > 0:
                print(f"rtl_433 termino antes de tiempo ({elapsed:.1f}s). Esperando {wait_more:.1f}s...")
                time.sleep(wait_more)
        metrics = extract_metrics(
            output,
            args.min_count,
            require_model=not args.no_model_filter,
            min_pulse_total=args.min_pulse_total,
            min_total_count=args.min_total_count,
            model_window=args.model_window,
            min_long_gap=args.min_long_gap,
        )
        if not metrics:
            missed += 1
            stable = 0
            print("No se pudieron extraer métricas de la captura.")
            if args.dump_on_miss:
                with open(args.dump_on_miss, "w", encoding="utf-8", errors="replace") as f:
                    f.write(output)
                print(f"Salida de rtl_433 guardada en: {args.dump_on_miss}")
            if args.reupload_last_good and last_good and missed >= args.miss_reupload_threshold:
                print(f"Re-subiendo ultimo timing valido: hi={last_good[0]} lo={last_good[1]} gap={last_good[2]}")
                write_timings(sketch_file, last_good[0], last_good[1], last_good[2])
                if args.manual_upload:
                    print("Timings escritos. Sube manualmente con Arduino IDE 2.")
                else:
                    print("Compilando...")
                    code, out = run_cmd(f"{args.arduino_cli} compile --fqbn {args.fqbn} {sketch_dir}")
                    if code != 0:
                        print(out)
                        return code
                    if not prepare_for_upload(args):
                        print("Fallo en power cycle. Saliendo.")
                        return 2
                    upload_cmd = f"{args.arduino_cli} upload --fqbn {args.fqbn} {sketch_dir}"
                    if args.port:
                        upload_cmd += f" -p {args.port}"
                    print("Conecta el Digispark cuando el uploader lo pida.")
                    code, out = run_cmd(upload_cmd)
                    print(out)
                    if code != 0:
                        return code
                    time.sleep(args.post_upload_wait)
                missed = 0
                continue
            if args.continue_on_miss or args.max_missed == 0:
                print("Continuando sin cambios en timings.")
                continue
            if missed >= args.max_missed:
                print("Revirtiendo a timings de respaldo y saliendo.")
                write_timings(sketch_file, args.fallback_high, args.fallback_low, args.fallback_gap)
                print(f"Fallback: hi={args.fallback_high} lo={args.fallback_low} gap={args.fallback_gap}")
                if args.manual_upload:
                    print("Timings escritos. Sube manualmente con Arduino IDE 2.")
                    return 0
                print("Compilando...")
                code, out = run_cmd(f"{args.arduino_cli} compile --fqbn {args.fqbn} {sketch_dir}")
                if code != 0:
                    print(out)
                    return code
                if not prepare_for_upload(args):
                    print("Fallo en power cycle. Saliendo.")
                    return 2
                upload_cmd = f"{args.arduino_cli} upload --fqbn {args.fqbn} {sketch_dir}"
                if args.port:
                    upload_cmd += f" -p {args.port}"
                print("Conecta el Digispark cuando el uploader lo pida.")
                code, out = run_cmd(upload_cmd)
                print(out)
                return code
            print("Reintentando...")
            continue

        missed = 0
        last_good = (hi, lo, gap)
        print(f"Medido short_high={metrics['short_high']} short_low={metrics['short_low']} long_gap={metrics['long_gap']}")

        within_high = abs(metrics["short_high"] - args.target_high) <= args.tolerance_high
        within_low = abs(metrics["short_low"] - args.target_low) <= args.tolerance_low
        if metrics["long_gap"] is None:
            within_gap = True
        else:
            within_gap = abs(metrics["long_gap"] - args.target_gap) <= args.tolerance_gap

        if within_high and within_low and within_gap:
            stable += 1
        else:
            stable = 0

        if stable >= args.stable_iterations:
            print(
                "TIMING PERFECTO: dentro de tolerancia "
                f"{args.stable_iterations} iteraciones seguidas."
            )
            return 0

        new_hi = adjust(hi, metrics["short_high"], args.target_high, args.gain, args.max_step, 300, 900)
        new_lo = adjust(lo, metrics["short_low"], args.target_low, args.gain, args.max_step, 300, 900)
        if metrics["long_gap"] is not None:
            new_gap = adjust(gap, metrics["long_gap"], args.target_gap, args.gap_gain, args.gap_max_step, 2000, 20000)
        else:
            new_gap = gap

        with open(log_path, "a", encoding="ascii") as f:
            ts = dt.datetime.now().isoformat(timespec="seconds")
            f.write(f"{ts},{metrics['short_high']},{metrics['short_low']},{metrics['long_gap']},{metrics['reset_limit']},{new_hi},{new_lo},{new_gap}\n")

        if (new_hi, new_lo, new_gap) == (hi, lo, gap):
            print("Sin cambios en timings. Continuando captura para confirmar.")

        write_timings(sketch_file, new_hi, new_lo, new_gap)
        print(f"Nuevos timings: hi={new_hi} lo={new_lo} gap={new_gap}")

        if args.manual_upload:
            print("Timings escritos. Sube manualmente con Arduino IDE 2.")
            break

        print("Compilando...")
        code, out = run_cmd(f"{args.arduino_cli} compile --fqbn {args.fqbn} {sketch_dir}")
        if code != 0:
            print(out)
            return code

        if not prepare_for_upload(args):
            print("Fallo en power cycle. Saliendo.")
            return 2
        upload_cmd = f"{args.arduino_cli} upload --fqbn {args.fqbn} {sketch_dir}"
        if args.port:
            upload_cmd += f" -p {args.port}"
        print("Conecta el Digispark cuando el uploader lo pida.")
        code, out = run_cmd(upload_cmd)
        print(out)
        if code != 0:
            return code

        print("Esperando 5s antes de la siguiente captura...")
        time.sleep(5)

    print("Listo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
