# 01 - Data Capture / Captura de Datos

Scripts para capturar y procesar tramas del sensor Oregon Scientific THN132N.

## Scripts

### `logger_ec40.py`
Captura tramas en tiempo real desde el sensor y las guarda en CSV.

**Uso:**
```bash
python3 logger_ec40.py
```

### `merge_ec40_csvs.py`
Fusiona múltiples archivos CSV de capturas en un único archivo consolidado.

**Uso:**
```bash
python3 merge_ec40_csvs.py file1.csv file2.csv ... -o output.csv
```

## Datasets

Los datasets CSV se encuentran en el directorio raíz de `ec40_lut_suite/`:

- **`ec40_live.csv`** - Capturas en tiempo real (~120 tramas)
- **`ec40_capturas_merged.csv`** - Dataset consolidado (2197 tramas, 8 house IDs, -16°C a 61°C)

## Formato CSV

```
timestamp,raw168_hex,ec40_hex,temp_c,channel,house,battery,sync,id,r12_hex
2025-12-03 17:51:04,555555559995a5a6aa6aa6a9a9966a9aaaa55a5999,ec4014886120c3ba,21.8,1,132,1,0xE,0x40,0xC3B
```

## Notas

- Las capturas se realizan con receptor RTL-SDR u OOK demodulator
- Cada trama contiene: timestamp, datos raw, datos decodificados, temperatura, etc.
- El merge elimina duplicados y ordena por timestamp
