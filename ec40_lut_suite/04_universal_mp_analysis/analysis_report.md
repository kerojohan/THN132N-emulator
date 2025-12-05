# Informe d'anàlisi de taules M i P

**Total registres nets:** 741
**House codes únics:** 15

## Resum per House Code

| House | Mostres | Temp Min | Temp Max | Rang |
|-------|---------|----------|----------|------|
|  18 |   56 |   19.4°C |   36.1°C |  16.7°C |
|  39 |   15 |   13.3°C |   16.8°C |   3.5°C |
|  44 |    2 |   17.5°C |   17.5°C |   0.0°C |
|  53 |   36 |   13.3°C |   20.2°C |   6.9°C |
|  71 |   30 |    9.8°C |   16.1°C |   6.3°C |
|  94 |    4 |   19.0°C |   19.1°C |   0.1°C |
|  95 |   81 |   11.6°C |   23.9°C |  12.3°C |
| 121 |   94 |   13.0°C |   26.4°C |  13.4°C |
| 124 |   70 |   12.9°C |   25.2°C |  12.3°C |
| 131 |   44 |   12.8°C |   26.3°C |  13.5°C |
| 173 |   93 |   18.0°C |   36.3°C |  18.3°C |
| 184 |   46 |   12.4°C |   23.8°C |  11.4°C |
| 187 |   55 |   12.5°C |   25.1°C |  12.6°C |
| 205 |   65 |   11.6°C |   28.7°C |  17.1°C |
| 232 |   50 |   12.9°C |   27.6°C |  14.7°C |

## Troballes

### 1. Dades disponibles

- Tens dades de **15 house IDs diferents**
- El rang total de temperatura és de 9.8°C a 36.3°C

### 2. Problema de superposició

Per poder analitzar patrons XOR entre diferents house codes, necessitem:
- **Mateix rang de temperatures** per comparar els valors M i P
- **Prou mostres** en el rang compartit

#### Anàlisi de superposició entre house codes:

Parells amb bona superposició (>5 punts):

- House 95 vs House 121: 52 punts de temperatura en comú
- House 121 vs House 124: 48 punts de temperatura en comú
- House 95 vs House 124: 38 punts de temperatura en comú
- House 95 vs House 187: 37 punts de temperatura en comú
- House 121 vs House 187: 36 punts de temperatura en comú
- House 18 vs House 95: 29 punts de temperatura en comú
- House 121 vs House 232: 29 punts de temperatura en comú
- House 95 vs House 232: 28 punts de temperatura en comú
- House 124 vs House 131: 26 punts de temperatura en comú
- House 124 vs House 184: 26 punts de temperatura en comú

### 3. Anàlisi de taula M

Basant-nos en estudis anteriors (House 3 vs House 96):
- La taula M segueix un patró XOR **condicional**
- Sembla dependre del house_code i possiblement de la temperatura

### 4. Anàlisi de taula P

Basant-nos en estudis anteriors (House 3 vs House 247):
- La taula P sembla seguir un patró XOR **constant**
- `P_house2 = P_house1 XOR (constant)`

## Propostes per continuar l'anàlisi

### Opció 1: Captlades dirigides
1. Triar 2-3 house IDs
2. Capturar dades de cadascun en el **mateix rang de temperatures** (ex: 15-30°C)
3. Analitzar els patrons XOR amb dades comparables

### Opció 2: Anàlisi teòrica
1. Estudiar el codi font del THN132N (si està disponible)
2. Analitzar com es generen les taules M i P internament
3. Implementar una funció que reprodueixi aquest càlcul

### Opció 3: Enginyeria inversa amb les dades existents
1. Utilitzar les parells amb millor superposició
2. Analitzar patrons dins de cada house code
3. Buscar relacions amb altres paràmetres (rolling_code, etc.)

