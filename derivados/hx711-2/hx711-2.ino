/*
 * ESP32-C3 Super Mini + HX711 + MQTT Home Assistant
 * 
 * Envía peso por MQTT al conectarse al WiFi
 * Deep sleep entre mediciones para ahorro de energía
 *
 * Conexiones ESP32-C3 <-> HX711:
 *   HX711 DOUT (DT) -> GPIO2
 *   HX711 SCK  (CLK)-> GPIO1
 *   HX711 VCC       -> 3.3V
 *   HX711 GND       -> GND
 *
 * Librerías necesarias:
 *   - HX711 by bogde
 *   - PubSubClient by Nick O'Leary
 *   - ArduinoJson by Benoit Blanchon
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <HX711.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <ArduinoOTA.h>
#include "driver/rmt_tx.h"
#include "driver/gpio.h"
#include <time.h>
#include "config.h"

// -------------------- Objetos globales --------------------
HX711 balanza;
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// -------------------- RTC Memory para persistencia --------------------
RTC_DATA_ATTR int bootCount = 0;
RTC_DATA_ATTR uint64_t nextTempEpoch = 0;
RTC_DATA_ATTR float lastTempC = NAN;
RTC_DATA_ATTR bool lastTempValid = false;

static bool g_timeOk = false;
static uint32_t g_tempPeriodSec = 0;
static uint32_t g_feederEverySlots = 1;

// -------------------- Estructura para lectura estable --------------------
struct LecturaEstable {
  float peso;
  bool esValida;
  float desviacion;
  int numLecturas;
};

// -------------------- Prototipos --------------------
void conectarWiFi();
void conectarMQTT();
bool mqttPublishRetained(const char* topic, const char* payload, bool retained = true);
void publicarDiscoveryMQTT();
LecturaEstable obtenerPesoEstable();
void publicarPesoMQTT(LecturaEstable lectura);
float calcularDesviacionEstandar(float* valores, int n, float media);
void entrarDeepSleep(uint64_t tiempoSegundos);
void sincronizarNTP();
uint64_t calcularProximoDespertar();
bool obtenerTemperaturaHA(float &tempC);
void setupRmt();
void sendOregonFrame(float temp_c, uint8_t channel, uint8_t device_id, uint8_t nib7);
uint32_t getTempPeriodSec();
uint64_t align_next_epoch(uint64_t now, uint32_t period_sec);
void esperarHastaEpoch(uint64_t targetEpoch);
void iniciarOTA();
void ventanaOTA(uint32_t segundos);
void ejecutarCicloTempYFeeder();

void setup() {
  Serial.begin(115200);
  delay(500);
  
  bootCount++;
  Serial.println();
  Serial.println("================================");
  Serial.println("ESP32-C3 HX711 MQTT Feeder Scale");
  Serial.printf("Boot #%d\n", bootCount);
  Serial.println("================================");

  setupRmt();

  // ---- Conectar WiFi ----
  conectarWiFi();

  // ---- OTA por WiFi (ventana corta) ----
  if (OTA_ENABLED && OTA_WINDOW_SEC > 0) {
    iniciarOTA();
    ventanaOTA(OTA_WINDOW_SEC);
  }

  // ---- Sincronizar Hora NTP ----
  sincronizarNTP();
  uint64_t now = (uint64_t)time(nullptr);
  g_timeOk = (now > 1600000000ULL);
  
  g_tempPeriodSec = getTempPeriodSec();
  g_feederEverySlots = (FEEDER_PERIOD_SEC + (g_tempPeriodSec / 2)) / g_tempPeriodSec;
  if (g_feederEverySlots < 1) g_feederEverySlots = 1;
  uint64_t tempPrepEpoch = 0;
  if (g_timeOk) {
    if (nextTempEpoch == 0) nextTempEpoch = align_next_epoch(now, g_tempPeriodSec);
    tempPrepEpoch = (nextTempEpoch > TEMP_PREP_SEC) ? (nextTempEpoch - TEMP_PREP_SEC) : nextTempEpoch;
  }
  uint32_t currentSlot = g_timeOk ? (uint32_t)(nextTempEpoch / g_tempPeriodSec) : 0;
  bool publishFeeder = !g_timeOk ? true : (currentSlot % g_feederEverySlots == 0);
  bool sendTemp = true;
  Serial.printf("Temp period: %u s | Feeder period: %u s\n", g_tempPeriodSec, FEEDER_PERIOD_SEC);
  if (g_timeOk) {
    Serial.printf("Temp prep: %u s | Temp slot: %llu | Prep epoch: %llu\n",
                  TEMP_PREP_SEC, nextTempEpoch, tempPrepEpoch);
    Serial.printf("Feeder cada %u slots | Slot actual: %u\n", g_feederEverySlots, currentSlot);
  }
  Serial.printf("Temp send: %s | Feeder publish: %s\n",
                sendTemp ? "SI" : "no",
                publishFeeder ? "SI" : "no");
  
  // ---- Obtener temperatura desde Home Assistant ----
  if (sendTemp) {
    float tempC = NAN;
    bool tempOk = obtenerTemperaturaHA(tempC);
    if (!tempOk) {
      if (lastTempValid) {
        tempC = lastTempC;
        Serial.println("HA: temperatura no disponible, usando última conocida");
      } else {
        tempC = 0.0f;
        Serial.println("HA: temperatura no disponible y sin histórico, usando 0.0");
      }
    }
    
    if (tempOk) {
      tempC = roundf(tempC * 10.0f) / 10.0f;
      lastTempC = tempC;
      lastTempValid = true;
    }

    if (g_timeOk && now < nextTempEpoch) {
      Serial.printf("Esperando a epoch %llu para enviar temperatura\n", nextTempEpoch);
      esperarHastaEpoch(nextTempEpoch);
      now = (uint64_t)time(nullptr);
    }
    Serial.println("\n--- Enviando Oregon (FS1000A) ---");
    sendOregonFrame(tempC, OREGON_CHANNEL, OREGON_DEVICE_ID, OREGON_ROLLING_CODE);
    if (g_timeOk) {
      nextTempEpoch += g_tempPeriodSec;
    }
  }

  if (publishFeeder) {
    // ---- Inicializar HX711 ----
    Serial.println("\n--- Inicializando HX711 ---");
    balanza.begin(DOUT_PIN, SCK_PIN);
    
    if (!balanza.wait_ready_timeout(2000)) {
      Serial.println("ERROR: HX711 no detectado");
      Serial.println("Reintentando en 60 segundos...");
      entrarDeepSleep(60);
    }
    
    Serial.println("HX711 OK");
    balanza.set_scale(FACTOR_CALIBRACION);
    balanza.set_offset(OFFSET_LECTURA);
    
    // Debug para calibración inicial
    Serial.printf("Offset configurado: %ld\n", OFFSET_LECTURA);
    Serial.printf("Valor bruto actual (Raw): %ld\n", balanza.read());
    Serial.println("Báscula lista (Calibración fija)");
    
    // ---- Conectar MQTT ----
    mqttClient.setBufferSize(512); // Asegurar buffer para Discovery
    conectarMQTT();
    
    // ---- Publicar Discovery para Home Assistant ----
    publicarDiscoveryMQTT();
    
    // ---- Verificar conexión MQTT ----
    if (!mqttClient.connected()) {
      Serial.println("\n--- MQTT desconectado, reconectando... ---");
      conectarMQTT();
    }
    
    // ---- Obtener valor bruto para calibración ----
    Serial.println("\n--- Calibración ---");
    if (balanza.wait_ready_timeout(2000)) {
      long rawValue = balanza.read_average(10);
      Serial.printf("DEBUG: Raw promedio (10): %ld\n", rawValue);
      Serial.println("DEBUG: Si la balanza está VACÍA, copia este número en config.h:");
      Serial.printf("const long OFFSET_LECTURA = %ldL;\n", rawValue);
      Serial.println("DEBUG: Si hay peso conocido, guarda este raw para calcular FACTOR_CALIBRACION:");
      Serial.println("FACTOR_CALIBRACION = (raw_con_peso - raw_vacio) / peso_g");
    } else {
      Serial.println("ERROR: Sensor no listo para lectura de calibración");
    }
    
    // ---- Obtener peso estable y publicar ----
    Serial.println("\n--- Midiendo Peso ---");
    LecturaEstable resultado = obtenerPesoEstable();
    
    // Prioridad: emitir temperatura primero y luego publicar el comedero
    publicarPesoMQTT(resultado);
  }
  
  // ---- Calcular próximo despertar y dormir ----
  uint64_t segundosSueno = calcularProximoDespertar();
  
  // ---- Desconectar y preparar deep sleep ----
  mqttClient.disconnect();
  WiFi.disconnect(true);
  
  if (USE_DEEP_SLEEP) {
    if (g_timeOk) {
      now = (uint64_t)time(nullptr);
      while (nextTempEpoch <= now) nextTempEpoch += g_tempPeriodSec;
      uint64_t nextWake = (nextTempEpoch > TEMP_PREP_SEC) ? (nextTempEpoch - TEMP_PREP_SEC) : nextTempEpoch;
      uint64_t sleepSec = (nextWake > now) ? (nextWake - now) : 1;
      Serial.printf("Sleep until epoch %llu (in %llu s)\n", nextWake, sleepSec);
      entrarDeepSleep(sleepSec);
    } else {
      entrarDeepSleep(segundosSueno);
    }
  } else {
    Serial.println("Deep sleep desactivado: modo continuo");
  }
}

void loop() {
  if (USE_DEEP_SLEEP) {
    // Vacío - todo se ejecuta en setup() debido a deep sleep
    return;
  }
  ejecutarCicloTempYFeeder();
  delay(50);
}

// -------------------- Funciones --------------------
void ejecutarCicloTempYFeeder() {
  uint64_t now = (uint64_t)time(nullptr);
  if (!g_timeOk || now < 1600000000ULL) {
    sincronizarNTP();
    now = (uint64_t)time(nullptr);
    g_timeOk = (now > 1600000000ULL);
    if (g_timeOk && nextTempEpoch == 0) {
      g_tempPeriodSec = getTempPeriodSec();
      g_feederEverySlots = (FEEDER_PERIOD_SEC + (g_tempPeriodSec / 2)) / g_tempPeriodSec;
      if (g_feederEverySlots < 1) g_feederEverySlots = 1;
      nextTempEpoch = align_next_epoch(now, g_tempPeriodSec);
    }
  }

  if (g_timeOk) {
    uint64_t prepEpoch = (nextTempEpoch > TEMP_PREP_SEC) ? (nextTempEpoch - TEMP_PREP_SEC) : nextTempEpoch;
    if (now < prepEpoch) {
      return;
    }
  }

  conectarWiFi();

  float tempC = NAN;
  bool tempOk = obtenerTemperaturaHA(tempC);
  if (!tempOk) {
    if (lastTempValid) {
      tempC = lastTempC;
      Serial.println("HA: temperatura no disponible, usando última conocida");
    } else {
      tempC = 0.0f;
      Serial.println("HA: temperatura no disponible y sin histórico, usando 0.0");
    }
  }
  if (tempOk) {
    tempC = roundf(tempC * 10.0f) / 10.0f;
    lastTempC = tempC;
    lastTempValid = true;
  }

  if (g_timeOk && now < nextTempEpoch) {
    Serial.printf("Esperando a epoch %llu para enviar temperatura\n", nextTempEpoch);
    esperarHastaEpoch(nextTempEpoch);
    now = (uint64_t)time(nullptr);
  }
  Serial.println("\n--- Enviando Oregon (FS1000A) ---");
  sendOregonFrame(tempC, OREGON_CHANNEL, OREGON_DEVICE_ID, OREGON_ROLLING_CODE);

  if (g_timeOk) {
    uint32_t slot = (uint32_t)(nextTempEpoch / g_tempPeriodSec);
    bool publishFeeder = (slot % g_feederEverySlots == 0);
    if (publishFeeder) {
      // ---- Inicializar HX711 ----
      Serial.println("\n--- Inicializando HX711 ---");
      balanza.begin(DOUT_PIN, SCK_PIN);
      
      if (!balanza.wait_ready_timeout(2000)) {
        Serial.println("ERROR: HX711 no detectado");
      } else {
        Serial.println("HX711 OK");
        balanza.set_scale(FACTOR_CALIBRACION);
        balanza.set_offset(OFFSET_LECTURA);
        
        Serial.printf("Offset configurado: %ld\n", OFFSET_LECTURA);
        Serial.printf("Valor bruto actual (Raw): %ld\n", balanza.read());
        Serial.println("Báscula lista (Calibración fija)");
        
        mqttClient.setBufferSize(512);
        conectarMQTT();
        publicarDiscoveryMQTT();
        if (!mqttClient.connected()) {
          Serial.println("\n--- MQTT desconectado, reconectando... ---");
          conectarMQTT();
        }
        
        Serial.println("\n--- Calibración ---");
        if (balanza.wait_ready_timeout(2000)) {
          long rawValue = balanza.read_average(10);
          Serial.printf("DEBUG: Raw promedio (10): %ld\n", rawValue);
          Serial.println("DEBUG: Si la balanza está VACÍA, copia este número en config.h:");
          Serial.printf("const long OFFSET_LECTURA = %ldL;\n", rawValue);
          Serial.println("DEBUG: Si hay peso conocido, guarda este raw para calcular FACTOR_CALIBRACION:");
          Serial.println("FACTOR_CALIBRACION = (raw_con_peso - raw_vacio) / peso_g");
        } else {
          Serial.println("ERROR: Sensor no listo para lectura de calibración");
        }
        
        Serial.println("\n--- Midiendo Peso ---");
        LecturaEstable resultado = obtenerPesoEstable();
        publicarPesoMQTT(resultado);
      }
      mqttClient.disconnect();
    }
    nextTempEpoch += g_tempPeriodSec;
  }
}
void iniciarOTA() {
  ArduinoOTA.setHostname(OTA_HOSTNAME);
  if (OTA_PASSWORD && strlen(OTA_PASSWORD) > 0) {
    ArduinoOTA.setPassword(OTA_PASSWORD);
  }

  ArduinoOTA
    .onStart([]() {
      Serial.println("OTA: inicio");
    })
    .onEnd([]() {
      Serial.println("OTA: fin");
    })
    .onProgress([](unsigned int progreso, unsigned int total) {
      uint8_t pct = (total > 0) ? (progreso * 100 / total) : 0;
      Serial.printf("OTA: %u%%\n", pct);
    })
    .onError([](ota_error_t error) {
      Serial.printf("OTA: error %u\n", (unsigned)error);
    });

  ArduinoOTA.begin();
  Serial.printf("OTA: listo (%s)\n", OTA_HOSTNAME);
}

void ventanaOTA(uint32_t segundos) {
  Serial.printf("OTA: ventana %u s\n", segundos);
  const uint32_t inicio = millis();
  while ((millis() - inicio) < (segundos * 1000UL)) {
    ArduinoOTA.handle();
    delay(10);
  }
}

bool mqttPublishRetained(const char* topic, const char* payload, bool retained) {
  // PubSubClient devuelve false si no pudo meter el paquete en el buffer o si no está conectado
  for (int i = 0; i < 3; i++) {
    mqttClient.loop();
    if (mqttClient.publish(topic, payload, retained)) {
      // Dar margen al envío
      for (int k = 0; k < 5; k++) { 
        mqttClient.loop(); 
        delay(20); 
      }
      return true;
    }
    delay(150);
  }
  return false;
}

void conectarWiFi() {
  Serial.println("\n--- Conectando WiFi ---");
  Serial.printf("SSID: %s\n", WIFI_SSID);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int intentos = 0;
  while (WiFi.status() != WL_CONNECTED && intentos < 30) {
    delay(500);
    Serial.print(".");
    intentos++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi conectado!");
    Serial.printf("IP: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("RSSI: %d dBm\n", WiFi.RSSI());
  } else {
    Serial.println("\nERROR: No se pudo conectar a WiFi");
    Serial.println("Reintentando en 60 segundos...");
    entrarDeepSleep(60);
  }
}

void conectarMQTT() {
  Serial.println("\n--- Conectando MQTT ---");
  Serial.printf("Broker: %s:%d\n", MQTT_SERVER, MQTT_PORT);
  
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  
  int intentos = 0;
  while (!mqttClient.connected() && intentos < 5) {
    Serial.printf("Intento %d...\n", intentos + 1);
    
    bool conectado;
    if (strlen(MQTT_USER) > 0) {
      conectado = mqttClient.connect(MQTT_CLIENT_ID, MQTT_USER, MQTT_PASSWORD);
    } else {
      conectado = mqttClient.connect(MQTT_CLIENT_ID);
    }
    
    if (conectado) {
      Serial.println("MQTT conectado!");
      return;
    } else {
      Serial.printf("Error: %d\n", mqttClient.state());
      delay(2000);
      intentos++;
    }
  }
  
  Serial.println("ERROR: No se pudo conectar a MQTT");
}

LecturaEstable obtenerPesoEstable() {
  LecturaEstable resultado = {0, false, 0, 0};
  
  for (int intento = 0; intento < MAX_INTENTOS_ESTABILIDAD; intento++) {
    Serial.printf("\nIntento %d/%d\n", intento + 1, MAX_INTENTOS_ESTABILIDAD);
    
    float lecturas[NUM_LECTURAS_ESTABILIDAD];
    float suma = 0;
    
    // Tomar múltiples lecturas
    for (int i = 0; i < NUM_LECTURAS_ESTABILIDAD; i++) {
      if (balanza.wait_ready_timeout(1000)) {
        lecturas[i] = balanza.get_units(3);  // Promedio de 3 lecturas por muestra
        suma += lecturas[i];
        
        if (i % 5 == 0) Serial.print(".");
        delay(DELAY_ENTRE_LECTURAS_MS);
      } else {
        Serial.println("\nERROR: Timeout en lectura");
        return resultado;
      }
    }
    Serial.println();
    
    // Calcular media
    float media = suma / NUM_LECTURAS_ESTABILIDAD;
    
    // Calcular desviación estándar
    float desviacion = calcularDesviacionEstandar(lecturas, NUM_LECTURAS_ESTABILIDAD, media);
    
    Serial.printf("Media: %.2f g, Desviación: %.2f g\n", media, desviacion);
    
    // Verificar si es estable
    if (desviacion <= TOLERANCIA_GRAMOS) {
      resultado.peso = media;
      resultado.esValida = true;
      resultado.desviacion = desviacion;
      resultado.numLecturas = NUM_LECTURAS_ESTABILIDAD;
      Serial.println("✓ Lectura ESTABLE");
      return resultado;
    } else {
      Serial.printf("✗ Inestable (σ > %.1f g)\n", TOLERANCIA_GRAMOS);
      delay(1000);  // Esperar antes de reintentar
    }
  }
  
  // Si no se logró estabilidad, devolver última lectura
  Serial.println("ADVERTENCIA: No se logró estabilidad, usando última lectura");
  resultado.peso = balanza.get_units(20);
  resultado.esValida = false;
  resultado.numLecturas = NUM_LECTURAS_ESTABILIDAD;
  
  return resultado;
}

float calcularDesviacionEstandar(float* valores, int n, float media) {
  float sumaCuadrados = 0;
  
  for (int i = 0; i < n; i++) {
    float diff = valores[i] - media;
    sumaCuadrados += diff * diff;
  }
  
  return sqrt(sumaCuadrados / n);
}

void publicarPesoMQTT(LecturaEstable lectura) {
  if (!mqttClient.connected()) {
    Serial.println("ERROR: MQTT no conectado, no se puede publicar");
    return;
  }
  
  // Mantener conexión activa
  mqttClient.loop();
  
  Serial.println("\n--- Publicando a MQTT ---");
  
  // Crear JSON
  StaticJsonDocument<256> doc;
  float pesoPublicar = (lectura.peso < 0.0f) ? 0.0f : lectura.peso;
  doc["weight"] = round(pesoPublicar * 100) / 100.0;  // 2 decimales
  doc["unit"] = "g";
  doc["stable"] = lectura.esValida;
  doc["std_dev"] = round(lectura.desviacion * 100) / 100.0;
  doc["samples"] = lectura.numLecturas;
  doc["boot_count"] = bootCount;
  doc["rssi"] = WiFi.RSSI();
  
  // Serializar
  char jsonBuffer[256];
  serializeJson(doc, jsonBuffer);
  
  Serial.printf("Topic: %s\n", MQTT_TOPIC);
  Serial.printf("Payload: %s\n", jsonBuffer);
  
  // Publicar
  if (mqttClient.publish(MQTT_TOPIC, jsonBuffer, true)) {  // retained = true
    Serial.println("✓ Publicado exitosamente");
  } else {
    Serial.println("✗ Error al publicar");
  }
  
  // Dar tiempo para que se envíe completamente
  delay(500);
  mqttClient.loop();
}

void entrarDeepSleep(uint64_t tiempoSegundos) {
  Serial.println("\n--- Entrando en Deep Sleep ---");
  Serial.printf("Duración: %llu segundos (%.1f minutos)\n", 
                tiempoSegundos, tiempoSegundos / 60.0);
  Serial.println("================================");
  Serial.flush();
  
  // Configurar despertar por timer
  esp_sleep_enable_timer_wakeup(tiempoSegundos * 1000000ULL);  // microsegundos
  
  // Entrar en deep sleep
  esp_deep_sleep_start();
}

void sincronizarNTP() {
  Serial.println("\n--- Sincronizando hora NTP ---");
  configTime(GMT_OFFSET_SEC, DAYLIGHT_OFFSET_SEC, NTP_SERVER);
  
  struct tm timeinfo;
  int intentos = 0;
  while (!getLocalTime(&timeinfo) && intentos < 10) {
    Serial.print(".");
    delay(500);
    intentos++;
  }
  
  if (intentos < 10) {
    char timeString[64];
    strftime(timeString, sizeof(timeString), "%A, %B %d %Y %H:%M:%S", &timeinfo);
    Serial.println("\nHora sincronizada: " + String(timeString));
  } else {
    Serial.println("\nERROR: No se pudo obtener la hora NTP");
  }
}

uint64_t calcularProximoDespertar() {
  // Sincronizamos el ciclo con el ATtiny85THN132N_aht20:
  // Ch1 -> 39s, Ch2 -> 41s, Ch3 -> 43s (Ch3 se codifica como 4)
  uint64_t segundos = 43;
  if (OREGON_CHANNEL == 1) {
    segundos = 39;
  } else if (OREGON_CHANNEL == 2) {
    segundos = 41;
  } else if (OREGON_CHANNEL == 4) {
    segundos = 43;
  }
  Serial.printf("Intervalo de ciclo: %llu segundos\n", segundos);
  return segundos;
}

uint32_t getTempPeriodSec() {
  uint32_t segundos = 43;
  if (OREGON_CHANNEL == 1) {
    segundos = 39;
  } else if (OREGON_CHANNEL == 2) {
    segundos = 41;
  } else if (OREGON_CHANNEL == 4) {
    segundos = 43;
  }
  return segundos;
}

uint64_t align_next_epoch(uint64_t now, uint32_t period_sec) {
  uint64_t slots = now / period_sec;
  return (slots + 1) * (uint64_t)period_sec;
}

void esperarHastaEpoch(uint64_t targetEpoch) {
  while (true) {
    uint64_t now = (uint64_t)time(nullptr);
    if (now >= targetEpoch) break;
    uint64_t diff = targetEpoch - now;
    if (diff > 1) {
      delay(200);
    } else {
      delay(10);
    }
  }
}

// ---------------------------------------------------------------------------
// OREGON TX (FS1000A) - basado en oregon_transmitter_universal_aht20.ino
// ---------------------------------------------------------------------------

static const uint16_t P_TABLE[10] = {
  0x000, 0x075, 0x0EA, 0x09F, 0x0B5,
  0x0C0, 0x05F, 0x02A, 0x06B, 0x01E
};

static const int8_t  M_MIN_E = -16;
static const int8_t  M_MAX_E =  54;

static const uint16_t M_TABLE[71] = {
  0x2A1, 0x252, 0x203, 0x2B5, 0x2E4, 0x217, 0x246, 0x29A, // -16..-9
  0x2CB, 0x2F7, 0x2A6, 0x255, 0x204, 0x2B2, 0x2E3, 0x210, // -8..-1
  0x2C2, 0x148, 0x1BB, 0x1EA, 0x15C, 0x10D, 0x1FE, 0x1AF, // 0..7
  0x193, 0x1C2, 0x11E, 0x14F, 0x1BC, 0x236, 0x280, 0x10A, // 8..15
  0x1F9, 0x1A8, 0x194, 0x866, 0x2CC, 0x146, 0x1B5, 0x1E4, // 16..23
  0x152, 0x103, 0x1F0, 0x1A1, 0x246, 0x1CC, 0x110, 0x141, // 24..31
  0x1B2, 0x1E3, 0x8F6, 0x8A7, 0x854, 0x805, 0x839, 0x868, // 32..39
  0x8C6, 0x897, 0x864, 0x835, 0x883, 0x8D2, 0x821, 0x870, // 40..47
  0x84C, 0x81D, 0x162, 0x133, 0x863, 0x191, 0x884          // 48..54
};

static void temp_to_e_d(float temp_c, int &e, int &d) {
  e = (int)temp_c;
  float absT = fabsf(temp_c);
  int t10 = (int)roundf(absT * 10.0f);
  int abs_e = abs(e);
  d = t10 - abs_e * 10;
}

static uint16_t calc_R12(float temp_c) {
  int e, d;
  temp_to_e_d(temp_c, e, d);

  if (e < M_MIN_E) e = M_MIN_E;
  if (e > M_MAX_E) e = M_MAX_E;
  if (d < 0)       d = 0;
  if (d > 9)       d = 9;

  uint16_t P = P_TABLE[d];
  uint16_t M = M_TABLE[e - M_MIN_E];
  return (P ^ M) & 0x0FFF;
}

static uint8_t calc_os21_checksum(const uint8_t msg[8]) {
  uint8_t s = 0;
  for (int i = 0; i < 6; ++i) {
    uint8_t b = msg[i];
    s += (uint8_t)((b >> 4) + (b & 0x0F));
  }
  s &= 0xFF;
  uint8_t high = (s & 0xF0) >> 4;
  uint8_t low  = (s & 0x0F);
  return (uint8_t)((low << 4) | high);
}

static void temp_to_bcd_bytes(float temp_c, uint8_t &msg4, uint8_t &msg5) {
  uint8_t sign_bit = 0;
  if (temp_c < 0.0f) {
    sign_bit = 1;
    temp_c = -temp_c;
  }

  int t10 = (int)roundf(temp_c * 10.0f);
  int d0  = t10 % 10;
  int ent = t10 / 10;
  int u   = ent % 10;
  int d1  = (ent / 10) % 10;

  msg4 = (uint8_t)((d0 & 0x0F) << 4) | (uint8_t)(u & 0x0F);

  int hundreds      = 0;
  uint8_t lowNibble = (uint8_t)((sign_bit << 3) | (hundreds & 0x07));
  msg5 = (uint8_t)((d1 & 0x0F) << 4) | lowNibble;
}

static void build_ec40_post(float temp_c, uint8_t channel, uint8_t device_id, uint8_t msg[8]) {
  msg[0] = 0xEC;
  msg[1] = 0x40;

  uint8_t id_low  = (uint8_t)(device_id & 0x0F);
  uint8_t id_high = (uint8_t)(device_id & 0xF0);

  msg[2] = (uint8_t)(((channel & 0x0F) << 4) | id_low);
  msg[3] = id_high;

  temp_to_bcd_bytes(temp_c, msg[4], msg[5]);

  uint16_t r12 = calc_R12(temp_c);
  msg[3] = (uint8_t)((msg[3] & 0xF0) | ((r12 >> 8) & 0x0F));
  msg[7] = (uint8_t)(r12 & 0xFF);

  msg[6] = calc_os21_checksum(msg);
}

static void reflect_nibbles(const uint8_t *in, uint8_t *out, size_t len) {
  for (size_t i = 0; i < len; ++i) {
    uint8_t b = in[i];
    out[i] = (uint8_t)(((b & 0x0F) << 4) | (b >> 4));
  }
}

static void build_raw_from_payload(const uint8_t payload_bytes[8], char *out_hex) {
  uint8_t reflected[8];
  reflect_nibbles(payload_bytes, reflected, 8);

  const uint8_t header_bytes[5] = { 0x55, 0x55, 0x55, 0x55, 0x99 };
  
  uint8_t all_bits[168];
  int idx = 0;

  for (int i = 0; i < 5; ++i) {
    uint8_t b = header_bytes[i];
    for (int bit = 7; bit >= 0; --bit) {
      all_bits[idx++] = (uint8_t)((b >> bit) & 0x01);
    }
  }

  for (int bi = 0; bi < 8; ++bi) {
    uint8_t byte = reflected[bi];
    for (int j = 0; j < 8; ++j) {
      uint8_t bit = (uint8_t)((byte >> j) & 0x01);
      if (bit == 0) {
        all_bits[idx++] = 1;
        all_bits[idx++] = 0;
      } else {
        all_bits[idx++] = 0;
        all_bits[idx++] = 1;
      }
    }
  }

  const char HEXC[] = "0123456789ABCDEF";
  int out_pos = 0;
  for (int i = 0; i < 168; i += 8) {
    uint8_t val = 0;
    for (int j = 0; j < 8; ++j) {
      val |= (uint8_t)(all_bits[i + j] << (7 - j));
    }
    out_hex[out_pos++] = HEXC[(val >> 4) & 0x0F];
    out_hex[out_pos++] = HEXC[val & 0x0F];
  }
  out_hex[out_pos] = '\0';
}

static void hex_string_to_bits(const char* hex, uint8_t* bits, int& bitlen) {
  bitlen = 0;
  while (*hex && *(hex + 1)) {
    char byte_str[3] = {hex[0], hex[1], 0};
    uint8_t byte = (uint8_t)strtol(byte_str, nullptr, 16);
    for (int i = 7; i >= 0; i--) {
      bits[bitlen++] = (byte >> i) & 0x01;
    }
    hex += 2;
  }
}

static void build_raw_ook_frame(const char* hexstr, rmt_symbol_word_t* items, int& length) {
  uint8_t bits[512];
  int bitlen = 0;
  hex_string_to_bits(hexstr, bits, bitlen);

  int idx = 0;
  for (int i = 0; i < bitlen; i++) {
    if (bits[i]) {
      // 1: HIGH luego LOW (asimétrico)
      items[idx].level0 = 1;
      items[idx].duration0 = OREGON_HIGH_US;
      items[idx].level1 = 0;
      items[idx].duration1 = OREGON_LOW_US;
    } else {
      // 0: LOW luego HIGH (asimétrico)
      items[idx].level0 = 0;
      items[idx].duration0 = OREGON_LOW_US;
      items[idx].level1 = 1;
      items[idx].duration1 = OREGON_HIGH_US;
    }
    idx++;
  }
  length = idx;
}

static rmt_channel_handle_t tx_chan = NULL;
static rmt_encoder_handle_t copy_encoder = NULL;

void setupRmt() {
  rmt_tx_channel_config_t tx_config = {
    .gpio_num = (gpio_num_t)TX_GPIO,
    .clk_src = RMT_CLK_SRC_DEFAULT,
    .resolution_hz = 1000000, // 1 tick = 1 us
    .mem_block_symbols = 64,
    .trans_queue_depth = 4,
  };

  ESP_ERROR_CHECK(rmt_new_tx_channel(&tx_config, &tx_chan));
  rmt_copy_encoder_config_t copy_cfg = {};
  ESP_ERROR_CHECK(rmt_new_copy_encoder(&copy_cfg, &copy_encoder));
  ESP_ERROR_CHECK(rmt_enable(tx_chan));
}

void sendOregonFrame(float temp_c, uint8_t channel, uint8_t device_id, uint8_t nib7) {
  (void)nib7;
  uint8_t payload_bytes[8];
  build_ec40_post(temp_c, channel, device_id, payload_bytes);
  
  char raw_hex[43];
  build_raw_from_payload(payload_bytes, raw_hex);

  Serial.print(F("Temp: "));
  Serial.print(temp_c, 1);
  Serial.print(F("°C, CH: "));
  Serial.print(channel);
  Serial.print(F(", House: "));
  Serial.println(device_id);
  
  rmt_symbol_word_t items[512];
  int item_len = 0;
  build_raw_ook_frame(raw_hex, items, item_len);

  delayMicroseconds(OREGON_GAP_US);
  for (int i = 0; i < 2; i++) {
    rmt_transmit_config_t tx_cfg = {
      .loop_count = 0
    };
    ESP_ERROR_CHECK(rmt_transmit(tx_chan, copy_encoder, items,
                                 item_len * sizeof(rmt_symbol_word_t), &tx_cfg));
    ESP_ERROR_CHECK(rmt_tx_wait_all_done(tx_chan, -1));
    if (i < 1) {
      delayMicroseconds(OREGON_GAP_US);
    }
  }
}

bool obtenerTemperaturaHA(float &tempC) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("HA: WiFi no conectado");
    return false;
  }
  
  if (strlen(HA_TOKEN) == 0 || strlen(HA_TEMP_ENTITY_ID) == 0) {
    Serial.println("HA: Token o entity_id no configurado");
    return false;
  }
  
  String url = String(HA_URL) + "/api/states/" + HA_TEMP_ENTITY_ID;
  Serial.printf("\n--- Leyendo temperatura HA ---\nGET %s\n", url.c_str());
  
  HTTPClient http;
  http.begin(url);
  http.addHeader("Authorization", String("Bearer ") + HA_TOKEN);
  http.addHeader("Content-Type", "application/json");
  
  int code = http.GET();
  if (code != HTTP_CODE_OK) {
    Serial.printf("HA HTTP error: %d\n", code);
    http.end();
    return false;
  }
  
  String payload = http.getString();
  http.end();
  
  StaticJsonDocument<512> doc;
  DeserializationError err = deserializeJson(doc, payload);
  if (err) {
    Serial.printf("HA JSON error: %s\n", err.c_str());
    return false;
  }
  
  const char* state = doc["state"];
  if (!state) {
    Serial.println("HA: state vacío");
    return false;
  }
  if (!strcmp(state, "unknown") || !strcmp(state, "unavailable")) {
    Serial.printf("HA: state=%s\n", state);
    return false;
  }
  
  char* endPtr = nullptr;
  float value = strtof(state, &endPtr);
  if (endPtr == state) {
    Serial.printf("HA: state no numérico: %s\n", state);
    return false;
  }
  
  tempC = value;
  Serial.printf("HA: temperatura=%.2f C\n", tempC);
  return true;
}
