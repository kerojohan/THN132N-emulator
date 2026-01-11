# Oregon Scientific THN132N Emulator - Engineering Report

## Objective
To create a fully compatible clone of the Oregon Scientific THN132N temperature sensor using an **ATtiny85**. The emulator must not only transmit valid data decodeable by SDR (`rtl_433`), but physically synchronize and maintain connection with an official **Oregon Scientific BAR206 Weather Station**.

## Critical Findings

### 1. RF Physical Layer (The "Fingerprint")
Initial attempts with standard library timings (488µs) failed to pair with the BAR206 console, despite valid decoding by `rtl_433`. The console has much stricter physical layer tolerances.

Through iterative analysis with `rtl_433` and comparison with a genuine sensor (House Code 244), we optimized the timings to the microsecond.

**Final Verified Parameters (Channel 1):**
*   **HIGH Pulse:** `458 µs` (Target: 492µs, corrected for overhead)
*   **LOW Gap:** `512 µs` (Target: 476µs, corrected for overhead)
*   **Inter-Frame Gap:** `8188 µs` (Target: 8784µs, corrected for overhead)

*Note: The original profile was High~492/Low~476. Our emulator adds latency, so we drive the pin shorter (High) and wait longer (Low) to match the "air time" exactly.*

### 2. Transmission Interval (The "Heartbeat")
The most critical discovery was the **Synchronization Window**.
*   **Observed Behavior**: The console pairs initially but loses signal after ~1 minute.
*   **Cause**: The console opens a narrow reception window exactly every **39 seconds** (for Ch 1).
*   **Drift Analysis**:
    *   9 WDT Sleep Cycles = ~38 seconds (Too fast).
    *   10 WDT Sleep Cycles = ~43 seconds (Too slow).
*   **Solution**: A Hybrid Interval strategy.
    *   Sleep for 9 cycles (~38s) to save power.
    *   Wake up and perform a precision active `safe_delay(1000)` to synchronize exactly to 39s.

### 3. Universal Channel Logic
We implemented an adaptive loop that automatically adjusts the sleep/delay strategy based on the selected channel `g_channel`.

| Channel | Target Interval | Strategy (WDT Cycles + Active Delay) | Status |
| :--- | :--- | :--- | :--- |
| **Channel 1** | **39s** | **9 Cycles + 1000ms** | **VERIFIED PERFECT** |
| Channel 2 | 41s | 9 Cycles + 3000ms | *Pending Validation* |
| Channel 3 | 43s | 10 Cycles + 800ms | *Pending Validation* |

*Note: Channel 3 offers the theoretical maximum battery life as it naturally aligns with 10 WDT cycles, minimizing reliable active wait time.*

## Implementation Details (`safe_delay`)
Standard `delay()` caused timing drifts when mixed with the Watchdog Timer. We implemented `safe_delay(ms)` which periodically resets the Watchdog during the active wait loop (`wdt_reset()`), preventing accidental resets or counting overlaps.

```cpp
// Helper to delay without WDT timeout/overlap
void safe_delay(unsigned long ms) {
  unsigned long start = millis();
  while (millis() - start < ms) {
    wdt_reset();
  }
}
```

## Conclusion & Next Steps
**Channel 1 is fully functional and stable.**
The sensor reliably pairs and updates the BAR206 console.

**Future Work:**
- Validate and fine-tune active delays for Channels 2 and 3 using the same methodology if required.
- Further power profiling to see if the 1000ms active delay on Ch1 impacts battery life significantly compared to the "pure sleep" goal of Ch3.
