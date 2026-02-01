# PCB Placement Guide (2-layer) - 80mm x 45mm

Board outline: `docs/easyeda/board_outline_80x45.dxf`
Units: mm, origin at bottom-left (0,0).

## Suggested footprints (EasyEDA library)
- Headers: `HDR-1x2_2.54`, `HDR-1x3_2.54`, `HDR-1x4_2.54`, `HDR-1x6_2.54`
- P-MOSFET: `SOT-23`
- R/C: `0603` (or `0805` if you prefer)

## Module header placement (center coordinates)

### MT3608 header (H3, 1x4)
- Footprint: HDR-1x4_2.54
- Center: (15, 32)
- Orientation: horizontal (pins along X)

### TP4056 header (H2, 1x4)
- Footprint: HDR-1x4_2.54
- Center: (15, 12)
- Orientation: horizontal

### Battery header (H1, 1x2)
- Footprint: HDR-1x2_2.54
- Center: (5, 12)
- Orientation: vertical

### Digispark header (H4, 1x6)
- Footprint: HDR-1x6_2.54
- Center: (55, 12)
- Orientation: horizontal

### AHT10 header (H5, 1x4)
- Footprint: HDR-1x4_2.54
- Center: (55, 32)
- Orientation: horizontal

### FS1000A header (H6, 1x3)
- Footprint: HDR-1x3_2.54
- Center: (75, 32)
- Orientation: vertical

## MOSFET + passives placement
- Q1 (SOT-23) near 5V_SW rail: center (40, 28)
- R1 100k gate pull-up: center (40, 31)
- R2 100 ohm gate series: center (40, 25)
- Optional R3/R4 1k on SDA/SCL: centers (52, 28) and (52, 30)

## Decoupling caps
- C1 10uF + C3 100nF near MT3608: centers (20, 36) and (20, 39)
- C2 10uF near AHT10: center (55, 36)
- C4 10uF near FS1000A: center (75, 36)

## Net labels
Use the netlist in `docs/easyeda/attiny85_boost_netlist.txt` for wiring.

