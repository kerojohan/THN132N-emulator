# Guia Maestra de Tuning RF (Oregon THN132N + ATtiny85)

Aquest document resumeix tot el coneixement extret del procés d'enginyeria inversa i afinament per clonar un sensor Oregon Scientific THN132N. Utilitza-lo com a manual si mai has de canviar de xip ATtiny85 o ajustar un sensor nou.

---

## 1. El Problema de l'Oscil·lador Intern ⏱️
L'ATtiny85 no té un rellotge de precisió (cristall). El seu oscil·lador intern de 8MHz pot variar entre unitats depenent del voltatge i la temperatura.
- **Unitats "Accelerades":** Poden necessitar valors de `T_UNIT` molt baixos (ex: 340µs) per produir polsos reals de 500µs.
- **Unitats "Estàndard":** Solen moure's en valors més propers als teòrics (ex: 470-490µs).

**Lliçó:** Mai copiïs cegament les constants d'un xip a un altre. Sempre cal un cicle de calibratge amb `rtl_433`.

---

## 2. La "Signatura Física" (Timings) 📊
Perquè una consola BAR206 accepti el senyal, els temps han de ser gairebé perfectes.

| Paràmetre | Valor Objectiu | Descripció |
| :--- | :--- | :--- |
| **High Pulse** | **512 µs** | El temps que el transmissor està emetent. |
| **Low Gap** | **456 µs** | El temps buit entre semibits de la mateixa trama. |
| **Inter-Frame Gap** | **9248 µs** | El silenci crucial entre les dues repeticions del missatge. |

> [!TIP]
> Si el `rtl_433` detecta a 19.5°C però la consola no, el culpable sol ser el **Inter-Frame Gap**. La consola l'utilitza per saber on acaba el missatge i calcular el checksum.

---

## 3. Identitat i Seguretat (Payload) 🧬
El sensor THN132N utilitza un protocol especial (EC40) on la seguretat R12 depèn de la temperatura i del **House Code** (ID).
- **ID del Sensor:** Hem après que és millor **clonar l'ID del sensor original** (ex: 131) que intentar que la consola aprengui un de nou.
- **R12 Security:** Es calcula fent un XOR entre una taula P (decimals) i una taula M (enters). Les nostres taules han estat validades bit-a-bit contra un sensor real.

---

## 4. Estratègia de Sincronització (39s) ⏰
La consola obre la "finestra de recepció" exactament cada:
- **Canal 1:** 39 segons.
- **Canal 2:** 41 segons.
- **Canal 3:** 43 segons.

Com que el Watchdog Timer (WDT) de l'ATtiny només permet salts de 8 segons, hem creat una **Estratègia Híbrida**:
1. Dormir 9 cicles de WDT (~38 segons).
2. Fer un `safe_delay(1000)` actiu per arribar als 39s exactes.

---

## 5. Flux de Treball per a un nou ATtiny 🛠️
Si canvies de xip, segueix aquests passos:
1. **Flasheja el codi base** amb els valors de la "Unitat #2".
2. **Mesura amb `rtl_433 -A`** i mira el distributiu de polsos.
3. **Calcula l'Offset:**
   - Si el High mesurat és 508 i vols 512 (+4), puja la constant `HIGH_UNIT_US` en +4 punts.
   - Si el Gap mesurat és 9700 i vols 9248 (-452), baixa la constant `INTER_FRAME_GAP_US` en -450 punts aproximadament.
4. **Itera** fins que l'error sigui menor de 4µs.

---

## 6. Eines Crucials 🧰
- **`rtl_433 -A`**: L'única manera de veure la realitat física del senyal.
- **`auto_tune_improved.py`**: El script que ens ha permès fer 50 proves en una tarda sense tornar-nos bojos.
- **`safe_delay()`**: Imprescindible per mantenir la sincronització sense que el Watchdog resetegi el xip.

---
*Document creat el 18 de Gener de 2026. Missió: Clonatge Bit-Perfecte.*
