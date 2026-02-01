# ESP32-C3 HX711 MQTT Home Assistant Integration

Sistema de báscula inteligente con ESP32-C3 Super Mini y sensor HX711 que envía mediciones automáticas a Home Assistant vía MQTT.

## 📋 Características

- ✅ Conexión WiFi automática
- ✅ Publicación MQTT a Home Assistant
- ✅ Mediciones programadas (7:00 y 21:00)
- ✅ Lecturas estables con filtrado estadístico (±5g)
- ✅ Deep sleep para ahorro de energía
- ✅ Sincronización NTP para horarios precisos
- ✅ Formato JSON con metadata completa

## 🔌 Hardware

### Conexiones ESP32-C3 ↔ HX711

```
HX711 DOUT (DT) → GPIO2
HX711 SCK (CLK) → GPIO1
HX711 VCC       → 3.3V
HX711 GND       → GND
```

### Componentes

- **ESP32-C3 Super Mini**
- **HX711** - Amplificador para celda de carga
- **Celda de carga 5kg** (4 hilos: Rojo=E+, Negro=E-, Verde=A+, Blanco=A-)

## 📚 Librerías Necesarias

Instalar desde el Library Manager de Arduino IDE:

1. **HX711** by bogde
2. **PubSubClient** by Nick O'Leary
3. **ArduinoJson** by Benoit Blanchon
4. **ArduinoOTA** by Arduino

## ⚙️ Configuración

Editar `config.h` con tus credenciales:

```cpp
// WiFi
const char* WIFI_SSID = "TU_SSID";
const char* WIFI_PASSWORD = "TU_PASSWORD";

// MQTT
const char* MQTT_SERVER = "192.168.1.39";  // IP de Home Assistant
const char* MQTT_TOPIC = "feeder/weight";

// Horarios (24h)
const int HORA_MEDICION_1 = 7;   // 7:00 AM
const int HORA_MEDICION_2 = 21;  // 9:00 PM
```

### OTA (Arduino IDE)

- Configura `SECRET_OTA_PASSWORD` en `secrets.h` (opcional).
- Ajusta `OTA_WINDOW_SEC` en `config.h` para la ventana de actualización al arrancar.
- En el IDE, selecciona el puerto de red cuando el dispositivo esté dentro de la ventana OTA.

## 🚀 Uso

### Primera vez - Calibración

1. Usar el código original `esp32hx711.ino` para calibrar
2. Obtener el `factorCalibracion`
3. Actualizar el valor en `config.h`

### Modo automático

1. Subir `esp32hx711_mqtt.ino` al ESP32
2. El dispositivo:
   - Se conecta a WiFi
   - Sincroniza hora vía NTP
   - Toma medición estable
   - Publica a MQTT
   - Entra en deep sleep hasta próxima medición

## 📊 Formato MQTT

El dispositivo publica mensajes JSON en el topic `feeder/weight`:

```json
{
  "weight": 1234.56,
  "unit": "g",
  "stable": true,
  "std_dev": 2.34,
  "samples": 25,
  "boot_count": 42,
  "timestamp": "2025-12-31T07:00:00"
}
```

### Campos

- `weight`: Peso en gramos (2 decimales)
- `unit`: Unidad de medida
- `stable`: `true` si la desviación está dentro de tolerancia
- `std_dev`: Desviación estándar de las lecturas
- `samples`: Número de muestras tomadas
- `boot_count`: Contador de reinicios (debug)
- `timestamp`: Marca de tiempo ISO 8601

## 🏠 Configuración Home Assistant

### Sensor MQTT

Añadir a `configuration.yaml`:

```yaml
mqtt:
  sensor:
    - name: "Feeder Weight"
      state_topic: "feeder/weight"
      unit_of_measurement: "g"
      value_template: "{{ value_json.weight }}"
      json_attributes_topic: "feeder/weight"
      json_attributes_template: "{{ value_json | tojson }}"
      device_class: weight
      icon: mdi:scale
```

### Automatización ejemplo

```yaml
automation:
  - alias: "Alerta comida baja"
    trigger:
      - platform: mqtt
        topic: "feeder/weight"
    condition:
      - condition: template
        value_template: "{{ trigger.payload_json.weight < 500 }}"
    action:
      - service: notify.mobile_app
        data:
          message: "¡Comida baja! Solo quedan {{ trigger.payload_json.weight }}g"
```

## 🔋 Consumo de Energía

- **Activo** (medición + WiFi + MQTT): ~80-150mA durante ~30-60 segundos
- **Deep sleep**: ~10-20µA
- **Consumo diario estimado**: < 1mAh (con batería puede durar meses)

## 🛠️ Troubleshooting

### No se conecta a WiFi
- Verificar SSID y contraseña en `config.h`
- Comprobar que el ESP32 está en rango
- Revisar serial monitor para mensajes de error

### No publica a MQTT
- Verificar IP del broker MQTT
- Comprobar que Home Assistant tiene MQTT habilitado
- Si usa autenticación, configurar `MQTT_USER` y `MQTT_PASSWORD`

### Lecturas inestables
- Aumentar `NUM_LECTURAS_ESTABILIDAD` en `config.h`
- Aumentar `TOLERANCIA_GRAMOS` si el entorno es muy variable
- Verificar que la báscula está en superficie estable

### No despierta a la hora correcta
- Verificar sincronización NTP (revisar serial monitor)
- Ajustar `GMT_OFFSET_SEC` según tu zona horaria
- Configurar `DAYLIGHT_OFFSET_SEC` si aplica horario de verano

## 📁 Archivos

- `esp32hx711.ino` - Código original con calibración manual
- `esp32hx711_mqtt.ino` - Código MQTT automático ⭐
- `config.h` - Configuración WiFi/MQTT/horarios
- `README.md` - Esta documentación

## 📝 Notas

- El ESP32 entra en **deep sleep** entre mediciones, por lo que el puerto serial no estará disponible
- Para recalibrar, usar el código original `esp32hx711.ino`
- El factor de calibración actual: `-438.855133`
- Tolerancia de estabilidad: ±5g

## 🔗 Referencias

- [HX711 Library](https://github.com/bogde/HX711)
- [PubSubClient](https://github.com/knolleary/pubsubclient)
- [Home Assistant MQTT](https://www.home-assistant.io/integrations/mqtt/)
