/*
 * Configuración para ESP32-C3 HX711 MQTT Home Assistant
 */

#ifndef CONFIG_H
#define CONFIG_H

#include "secrets.h"

// -------------------- WiFi --------------------
const char* WIFI_SSID = SECRET_WIFI_SSID;
const char* WIFI_PASSWORD = SECRET_WIFI_PASSWORD;

// -------------------- Sleep --------------------
const bool USE_DEEP_SLEEP = false; // modo continuo para pruebas de timing

// -------------------- OTA (Arduino IDE) --------------------
const bool OTA_ENABLED = true;
const uint32_t OTA_WINDOW_SEC = 90;  // ventana de actualización al arrancar
const char* OTA_HOSTNAME = "esp32feeder";
#ifdef SECRET_OTA_PASSWORD
const char* OTA_PASSWORD = SECRET_OTA_PASSWORD;
#else
const char* OTA_PASSWORD = "";
#endif

// -------------------- MQTT --------------------
const char* MQTT_SERVER = "192.168.1.39";
const int MQTT_PORT = 1883;
const char* MQTT_USER = SECRET_MQTT_USER;  // Dejar vacío si no hay autenticación
const char* MQTT_PASSWORD = SECRET_MQTT_PASSWORD;  // Dejar vacío si no hay autenticación
const char* MQTT_TOPIC = "feeder/weight";
const char* MQTT_CLIENT_ID = "esp32feeder";
const char* DEVICE_NAME = "ESP32 MQTT Feeder Weight";
const char* MQTT_DISCOVERY_PREFIX = "homeassistant";

// -------------------- Home Assistant REST --------------------
const char* HA_URL = "http://192.168.1.39:8123";
#ifndef SECRET_HA_TOKEN
#define SECRET_HA_TOKEN "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI5OWZlNzY5YjAwMzM0NTY3YjllMzgwNDk4MGNiOGVmOSIsImlhdCI6MTc2OTg0NDkwNywiZXhwIjoyMDg1MjA0OTA3fQ.gdr2ulYw4ijILOeGexGyQuvWkRl1CDfFZtlwSsr9eV0"
#endif
const char* HA_TOKEN = SECRET_HA_TOKEN;
const char* HA_TEMP_ENTITY_ID = "sensor.bth01_9e69_temperature";

// -------------------- Feeder publish cadence --------------------
const uint32_t FEEDER_PERIOD_SEC = 3600; // publicar cada hora, alineado a reloj

// -------------------- Temperatura (prep antes del envío RF) --------------------
const uint32_t TEMP_PREP_SEC = 10; // margen para WiFi + HA antes del slot RF

// -------------------- Oregon TX (FS1000A) --------------------
const int TX_GPIO = 4;  // DATA pin del FS1000A
const uint8_t OREGON_CHANNEL = 1;
const uint8_t OREGON_DEVICE_ID = 144;
const uint8_t OREGON_ROLLING_CODE = 0x2;
const uint16_t OREGON_HIGH_US = 471;
const uint16_t OREGON_LOW_US  = 506;
const uint16_t OREGON_GAP_US  = 8714;

// -------------------- NTP --------------------
const char* NTP_SERVER = "pool.ntp.org";
const long GMT_OFFSET_SEC = 3600;  // GMT+1 (España)
const int DAYLIGHT_OFFSET_SEC = 0;  // Ajustar según horario de verano (0 o 3600)

// -------------------- Parámetros de medición --------------------
// La publicación del feeder se controla por ciclos de despertar.

// -------------------- HX711 Pines --------------------
const int DOUT_PIN = 2;  // GPIO2
const int SCK_PIN = 1;   // GPIO1

// -------------------- Calibración --------------------
const float FACTOR_CALIBRACION = -438.168f;
const long OFFSET_LECTURA = 15387L;  // Calibrado con balanza vacía

// -------------------- Parámetros de estabilidad --------------------
const int NUM_LECTURAS_ESTABILIDAD = 25;  // Número de lecturas para promediar
const float TOLERANCIA_GRAMOS = 30.0f;     // ±50g de tolerancia
const int MAX_INTENTOS_ESTABILIDAD = 3;   // Intentos para obtener lectura estable
const int DELAY_ENTRE_LECTURAS_MS = 100;  // Delay entre lecturas

#endif
