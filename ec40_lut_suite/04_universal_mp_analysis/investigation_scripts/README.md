# Scripts d'Investigació

Aquest directori conté tots els scripts utilitzats durant el procés d'investigació per descobrir les fórmules universals del protocol Oregon THN132N.

## ⚠️ IMPORTANT

**Aquests scripts NO són necessaris per utilitzar el generador final.**

Són part del procés d'investigació que va portar als descobriments documentats a `../Docs/`.

## Tipus d'Scripts

### Anàlisi (`analyze_*.py`)
Scripts per analitzar patrons en les dades capturades:
- Correlacions entre House ID i taules
- Patrons de nibbles
- Transformacions XOR
- Distribucions estadístiques

### Solvers (`solve_*.py`, `brute_force_*.py`)
Proves exhaustives d'algorismes:
- >20,000 variants de CRC
- Checksums (Fletcher, Adler, Luhn)
- Hash multiplicatius
- Combinacions compostes

### Tests (`test_*.py`, `verify_*.py`)
Scripts de verificació:
- Tests de hipòtesis
- Validacions de fórmules
- Comparacions amb captures reals

### Debug (`debug_*.py`, `clarify_*.py`)
Scripts de depuració durant la investigació:
- Anàlisi de casos especials
- Investigació de comportaments inesperats

### Utilitats (`generate_*.py`)
Generadors auxiliars:
- LUTs intermèdies
- Taules de verificació
- Reports

## Resultats

Els resultats finals de tota aquesta investigació estan documentats a:
- `../Docs/README.md` - Documentació completa
- `../Docs/p_algorithm_tests.md` - Detall de >20,000 proves
- `../Docs/oregon_p_lut_complete.py` - Solució final

## Ús

Si vols revisar el procés d'investigació, pots executar aquests scripts, però **no són necessaris per utilitzar el generador**.

Per utilitzar el generador final, consulta:
- `/esp32/oregon_transmitter_universal.ino` (Arduino)
- `../Docs/oregon_p_lut_complete.py` (Python)
