# Original Sensor RF Signature (Golden Sample)

Reference timings captured from the user's specific Oregon Scientific THN132N sensor.

## 🟢 Channel 1 (Primary Target)
**Used for validation and cloning.**

*   **Capture Date:** 2026-01-18 18:16:24
*   **House Code:** 62
*   **Channel:** 1

### Verified Timings
| Parameter | Value | Notes |
| :--- | :--- | :--- |
| **High Pulse** | **512 µs** | Short Pulse |
| **Low Gap** | **456 µs** | Short Gap |
| **Inter-Frame Gap** | **9248 µs** | Frame Gap |

### Evidence
```text
[ 1] count:   56,  width:  512 us [464;568]
[ 1] count:   56,  width:  456 us [420;504]
[ 2] count:    1,  width: 9248 us [9248;9248]
```

---

## 🟡 Channel 4 (Secondary Reference)
**Captured earlier, useful for comparison.**

*   **Capture Date:** 2026-01-18 18:10:51
*   **House Code:** 25
*   **Channel:** 4

### Verified Timings
| Parameter | Value | Notes |
| :--- | :--- | :--- |
| **High Pulse** | **488 µs** | Slightly shorter than Ch1 |
| **Low Gap** | **484 µs** | Slightly longer than Ch1 |
| **Inter-Frame Gap** | **8788 µs** | Shorter frame gap |

### Evidence
```text
[ 1] count:   68,  width:  488 us [440;536]
[ 1] count:   66,  width:  484 us [440;544]
[ 2] count:    1,  width: 8788 us [8788;8788]
```
