# EasyEDA Schematic Notes (Headers) - ATtiny85 + TP4056 + MT3608 + AHT10 + FS1000A

Goal: 18650 -> TP4056 -> MT3608 (5V boost) -> Digispark ATtiny85 + AHT10 + FS1000A.
Priority: low consumption. Use a P-MOSFET high-side switch to power AHT10/FS1000A.

## Power strategy
- Digispark is powered directly from MT3608 5V output (pin "5V", not VIN/RAW).
- AHT10 + FS1000A are powered from a switched rail (5V_SW) controlled by ATtiny.

## Control pin
- Use P3 (PB3) as ATtiny_PWR_CTRL.
- ATtiny_PWR_CTRL = LOW => P-MOSFET ON => 5V_SW enabled.
- ATtiny_PWR_CTRL = HIGH or FLOAT => P-MOSFET OFF => 5V_SW disabled.

## Recommended MOSFET
- P-MOSFET SOT-23: AO3407A (preferred), IRLML6402, SI2301.
- Gate pull-up: 100k to 5V_BOOST (keeps it off by default).
- Gate series resistor: 100 ohm from ATtiny to gate.

## Optional I2C back-power protection
- Add 1k in series on SDA and SCL between ATtiny and AHT10.

---

## Headers (use 2.54mm pin headers in EasyEDA)

### H1 - Battery 18650 (1x2)
- H1.1 BAT+
- H1.2 BAT-

### H2 - TP4056 module (1x4)
- H2.1 OUT+
- H2.2 OUT-
- H2.3 B+
- H2.4 B-

### H3 - MT3608 module (1x4)
- H3.1 VIN+
- H3.2 VIN-
- H3.3 VOUT+
- H3.4 VOUT-

### H4 - Digispark ATtiny85 (1x6)
- H4.1 5V
- H4.2 GND
- H4.3 P0 (PB0 / SCL)
- H4.4 P2 (PB2 / SDA)
- H4.5 P4 (PB4 / RF DATA)
- H4.6 P3 (PB3 / ATtiny_PWR_CTRL)

### H5 - AHT10 module (1x4)
- H5.1 VDD
- H5.2 GND
- H5.3 SDA
- H5.4 SCL

### H6 - FS1000A module (1x3)
- H6.1 VCC
- H6.2 GND
- H6.3 DATA

---

## Net labels
- BAT+, BAT-
- 5V_BOOST (MT3608 VOUT+)
- GND (MT3608 VOUT-)
- 5V_SW (switched 5V to AHT10 + FS1000A)
- ATtiny_PWR_CTRL
- AHT10_SDA, AHT10_SCL
- FS1000A_DATA

---

## Connection list (summary)
- BAT+  -> TP4056 B+
- BAT-  -> TP4056 B-
- TP4056 OUT+ -> MT3608 VIN+
- TP4056 OUT- -> MT3608 VIN-

- MT3608 VOUT+ -> 5V_BOOST
- MT3608 VOUT- -> GND

- Digispark 5V -> 5V_BOOST
- Digispark GND -> GND

- Digispark P0 (PB0) -> AHT10_SCL (optional series 1k)
- Digispark P2 (PB2) -> AHT10_SDA (optional series 1k)
- Digispark P4 (PB4) -> FS1000A_DATA
- Digispark P3 (PB3) -> ATtiny_PWR_CTRL

- P-MOSFET source -> 5V_BOOST
- P-MOSFET drain  -> 5V_SW
- P-MOSFET gate   -> ATtiny_PWR_CTRL
- Gate pull-up 100k -> 5V_BOOST
- Gate series 100 ohm -> ATtiny_PWR_CTRL

- AHT10 VDD -> 5V_SW
- AHT10 GND -> GND
- AHT10 SDA -> AHT10_SDA
- AHT10 SCL -> AHT10_SCL

- FS1000A VCC -> 5V_SW
- FS1000A GND -> GND
- FS1000A DATA -> FS1000A_DATA

---

## Decoupling (recommended)
- 10uF + 100nF near MT3608 VOUT (5V_BOOST to GND)
- 10uF + 100nF near AHT10 (5V_SW to GND)
- 10uF near FS1000A (5V_SW to GND)

