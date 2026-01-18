/*
 * ATtiny85 Oregon Scientific THN132N Emulator with AHT20 Sensor
 *
 * Hardware Connections:
 * - AHT20 SDA -> PB2
 * - AHT20 SCL -> PB0
 * - RF Data   -> PB4 (defined as RF_PIN)
 * - LED       -> PB1 (Built-in)
 *
 * Power Saving:
 * - Uses Watchdog Timer for deep sleep
 * - SoftI2C implementation for custom pins
 *
 * CAMBIO CLAVE:
 * - En RF ya NO usamos un solo T_UNIT para HIGH y LOW.
 * - Usamos HIGH_UNIT_US y LOW_UNIT_US distintos para clonar al original:
 *     short high ~508us, long high ~1012us
 *     short low  ~472us, long low  ~944us
 *   Esto suele marcar la diferencia con consolas (BAR206) aunque rtl_433 lo decodifique igual.
 */

#include <Arduino.h>
#include <avr/sleep.h>
#include <avr/wdt.h>
#include <avr/interrupt.h>
#include <math.h>

// ---------------------------------------------------------------------------
// CONFIGURATION
// ---------------------------------------------------------------------------
const uint8_t RF_PIN  = 4;  // PB4 RF transmitter
const uint8_t SDA_PIN = 2;  // PB2 AHT20 SDA
const uint8_t SCL_PIN = 0;  // PB0 AHT20 SCL

#ifndef LED_BUILTIN
#define LED_BUILTIN 1
#endif
#define LED_PIN LED_BUILTIN

#define LED_ON  HIGH
#define LED_OFF LOW

// Oregon Parameters
const uint8_t g_channel   = 1;  // Channel 3 (1=Ch1, 2=Ch2, 4=Ch3)
const uint8_t g_device_id = 131;   // CLONADO: ID del sensor original
// ---------------------------------------------------------------------------
// Ajustes finales para BATERÍA EXTERNA (Target: 512 / 456 / 9248):
const uint16_t HIGH_UNIT_US = 507;
const uint16_t LOW_UNIT_US  = 469;

// Gap “largo” entre tramas duplicadas
const uint16_t INTER_FRAME_GAP_US = 8764;

// ---------------------------------------------------------------------------
// TABLAS P[d] y M[e] (House 247)
// ---------------------------------------------------------------------------
const uint16_t P_TABLE[10] = {
  0x000, 0x075, 0x0EA, 0x09F, 0x0B5,
  0x0C0, 0x05F, 0x02A, 0x06B, 0x01E
};

const int8_t  M_MIN_E = -16;
const int8_t  M_MAX_E =  54;
const uint16_t M_TABLE[71] = {
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

// ---------------------------------------------------------------------------
// SOFT I2C
// ---------------------------------------------------------------------------
void i2c_init() {
  pinMode(SDA_PIN, INPUT_PULLUP);
  pinMode(SCL_PIN, INPUT_PULLUP);
}

void i2c_start() {
  pinMode(SDA_PIN, OUTPUT);
  digitalWrite(SDA_PIN, LOW);
  delayMicroseconds(5);
  pinMode(SCL_PIN, OUTPUT);
  digitalWrite(SCL_PIN, LOW);
}

void i2c_stop() {
  pinMode(SDA_PIN, OUTPUT);
  digitalWrite(SDA_PIN, LOW);
  pinMode(SCL_PIN, INPUT_PULLUP);
  delayMicroseconds(5);
  pinMode(SDA_PIN, INPUT_PULLUP);
  delayMicroseconds(5);
}

bool i2c_write(uint8_t data) {
  for (uint8_t i = 0; i < 8; i++) {
    if (data & 0x80) pinMode(SDA_PIN, INPUT_PULLUP);
    else { pinMode(SDA_PIN, OUTPUT); digitalWrite(SDA_PIN, LOW); }

    data <<= 1;
    delayMicroseconds(4);
    pinMode(SCL_PIN, INPUT_PULLUP);
    delayMicroseconds(5);
    pinMode(SCL_PIN, OUTPUT); digitalWrite(SCL_PIN, LOW);
    delayMicroseconds(4);
  }

  pinMode(SDA_PIN, INPUT_PULLUP);
  delayMicroseconds(4);
  pinMode(SCL_PIN, INPUT_PULLUP);
  delayMicroseconds(4);
  bool ack = !digitalRead(SDA_PIN);
  delayMicroseconds(4);
  pinMode(SCL_PIN, OUTPUT); digitalWrite(SCL_PIN, LOW);

  return ack;
}

uint8_t i2c_read(bool ack) {
  uint8_t data = 0;
  pinMode(SDA_PIN, INPUT_PULLUP);

  for (uint8_t i = 0; i < 8; i++) {
    data <<= 1;
    delayMicroseconds(4);
    pinMode(SCL_PIN, INPUT_PULLUP);
    delayMicroseconds(4);
    if (digitalRead(SDA_PIN)) data |= 1;
    delayMicroseconds(4);
    pinMode(SCL_PIN, OUTPUT); digitalWrite(SCL_PIN, LOW);
  }

  if (ack) { pinMode(SDA_PIN, OUTPUT); digitalWrite(SDA_PIN, LOW); }
  else pinMode(SDA_PIN, INPUT_PULLUP);

  delayMicroseconds(4);
  pinMode(SCL_PIN, INPUT_PULLUP);
  delayMicroseconds(5);
  pinMode(SCL_PIN, OUTPUT); digitalWrite(SCL_PIN, LOW);
  pinMode(SDA_PIN, INPUT_PULLUP);

  return data;
}

// ---------------------------------------------------------------------------
// AHT20
// ---------------------------------------------------------------------------
#define AHT20_ADDR 0x38

bool aht20_init_sensor() {
  i2c_init();
  delay(100);

  i2c_start();
  if (!i2c_write((AHT20_ADDR << 1) | 0)) { i2c_stop(); return false; }
  if (!i2c_write(0x71)) { i2c_stop(); return false; }
  i2c_stop();

  i2c_start();
  if (!i2c_write((AHT20_ADDR << 1) | 1)) { i2c_stop(); return false; }
  uint8_t status = i2c_read(false);
  i2c_stop();

  if (!(status & 0x08)) {
    i2c_start();
    i2c_write((AHT20_ADDR << 1) | 0);
    i2c_write(0xBE);
    i2c_write(0x08);
    i2c_write(0x00);
    i2c_stop();
    delay(10);
  }
  return true;
}

bool aht20_read(float &temp) {
  i2c_start();
  if (!i2c_write((AHT20_ADDR << 1) | 0)) { i2c_stop(); return false; }
  i2c_write(0xAC);
  i2c_write(0x33);
  i2c_write(0x00);
  i2c_stop();

  delay(100);

  i2c_start();
  if (!i2c_write((AHT20_ADDR << 1) | 1)) { i2c_stop(); return false; }

  uint8_t data[6];
  uint8_t status = i2c_read(true);

  if (status & 0x80) {
    i2c_read(false);
    i2c_stop();
    return false;
  }

  for (int i = 0; i < 5; i++) data[i] = i2c_read(true);
  data[5] = i2c_read(false);
  i2c_stop();

  uint32_t rawTemp = (((uint32_t)data[2] & 0x0F) << 16) | ((uint32_t)data[3] << 8) | data[4];
  temp = ((float)rawTemp * 200.0 / 1048576.0) - 50.0;
  return true;
}

// ---------------------------------------------------------------------------
// OREGON PROTOCOL LOGIC
// ---------------------------------------------------------------------------
void temp_to_e_d(float temp_c, int &e, int &d) {
  int sign = (temp_c < 0.0f) ? -1 : 1;
  float absT = fabsf(temp_c);
  int t10 = (int)roundf(absT * 10.0f);
  int ent = t10 / 10;
  e = sign * ent;
  d = t10 - ent * 10;
}

uint16_t calc_R12(float temp_c) {
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

void temp_to_bcd_bytes(float temp_c, uint8_t &msg4, uint8_t &msg5) {
  uint8_t sign_bit = 0;
  if (temp_c < 0.0f) { sign_bit = 1; temp_c = -temp_c; }
  int t10 = (int)roundf(temp_c * 10.0f);
  int d0  = t10 % 10;
  int ent = t10 / 10;
  int u   = ent % 10;
  int d1  = (ent / 10) % 10;
  msg4 = (uint8_t)((d0 & 0x0F) << 4) | (uint8_t)(u & 0x0F);
  uint8_t lowNibble = (uint8_t)((sign_bit << 3) | 0);
  msg5 = (uint8_t)((d1 & 0x0F) << 4) | lowNibble;
}

uint8_t calc_os21_checksum(const uint8_t msg[6]) {
  uint8_t s = 0;
  for (int i = 0; i < 6; ++i) {
    uint8_t b = msg[i];
    s += (uint8_t)((b >> 4) + (b & 0x0F));
  }
  uint8_t high = (s & 0xF0) >> 4;
  uint8_t low  = (s & 0x0F);
  return (uint8_t)((low << 4) | high);
}

void reflect_nibbles(const uint8_t *in, uint8_t *out, size_t len) {
  for (size_t i = 0; i < len; ++i) {
    uint8_t b = in[i];
    out[i] = (uint8_t)(((b & 0x0F) << 4) | (b >> 4));
  }
}

void build_ec40_post(float temp_c, uint8_t channel, uint8_t device_id, uint8_t msg[8]) {
  msg[0] = 0xEC;
  msg[1] = 0x40;
  uint8_t id_low  = device_id & 0x0F;
  uint8_t id_high = device_id & 0xF0;
  msg[2] = (uint8_t)(((channel & 0x0F) << 4) | id_low);
  msg[3] = id_high;

  temp_to_bcd_bytes(temp_c, msg[4], msg[5]);

  uint16_t r12 = calc_R12(temp_c);
  msg[3] = (uint8_t)((msg[3] & 0xF0) | ((r12 >> 8) & 0x0F));
  msg[7] = (uint8_t)(r12 & 0xFF);

  msg[6] = calc_os21_checksum(msg);
}

void build_osv21_bits_from_ec40_post(const uint8_t ec40_post[8], uint8_t all_bits[168]) {
  uint8_t ec40_pre[8];
  reflect_nibbles(ec40_post, ec40_pre, 8);

  const uint8_t header_bytes[5] = { 0x55, 0x55, 0x55, 0x55, 0x99 };

  int idx = 0;

  for (int i = 0; i < 5; ++i) {
    uint8_t b = header_bytes[i];
    for (int bit = 7; bit >= 0; --bit) {
      all_bits[idx++] = (uint8_t)((b >> bit) & 0x01);
    }
  }

  for (int bi = 0; bi < 8; ++bi) {
    uint8_t byte = ec40_pre[bi];
    for (int j = 0; j < 8; ++j) {
      uint8_t bit = (uint8_t)((byte >> j) & 0x01);
      if (bit == 0) { all_bits[idx++] = 1; all_bits[idx++] = 0; }
      else          { all_bits[idx++] = 0; all_bits[idx++] = 1; }
    }
  }
}

// ---------------------------------------------------------------------------
// RF TRANSMISSION
// ---------------------------------------------------------------------------
static inline void rf_high_low(uint16_t high_us, uint16_t low_us) {
  PORTB |=  (1 << RF_PIN);
  delayMicroseconds(high_us);
  PORTB &= ~(1 << RF_PIN);
  delayMicroseconds(low_us);
}

static inline void rf_low_high(uint16_t low_us, uint16_t high_us) {
  PORTB &= ~(1 << RF_PIN);
  delayMicroseconds(low_us);
  PORTB |=  (1 << RF_PIN);
  delayMicroseconds(high_us);
}

void send_bits_ook(const uint8_t *bits, int n_bits) {
  noInterrupts();
  for (int i = 0; i < n_bits; ++i) {
    if (bits[i]) {
      // 1: HIGH luego LOW (asimétrico)
      rf_high_low(HIGH_UNIT_US, LOW_UNIT_US);
    } else {
      // 0: LOW luego HIGH (asimétrico)
      rf_low_high(LOW_UNIT_US, HIGH_UNIT_US);
    }
  }
  PORTB &= ~(1 << RF_PIN);
  interrupts();
}

void sendOregonFrame(const uint8_t ec40_post[8]) {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LED_ON);

  uint8_t bits[168];
  build_osv21_bits_from_ec40_post(ec40_post, bits);

  // Como el original: 2 tramas
  send_bits_ook(bits, 168);
  delayMicroseconds(INTER_FRAME_GAP_US);
  send_bits_ook(bits, 168);

  digitalWrite(LED_PIN, LED_OFF);
  if (LED_PIN == SCL_PIN) pinMode(LED_PIN, INPUT_PULLUP);
}

// ---------------------------------------------------------------------------
// WATCHDOG / SLEEP
// ---------------------------------------------------------------------------
volatile uint8_t wdt_cycles = 0;

ISR(WDT_vect) { wdt_cycles++; }

void setup_watchdog() {
  cli();
  wdt_reset();
  MCUSR &= ~(1 << WDRF);
  WDTCR |= (1 << WDCE) | (1 << WDE);
  WDTCR = (1 << WDIE) | (1 << WDP3); // ~4s nominal
  sei();
}

void enter_sleep() {
  ADCSRA &= ~(1 << ADEN);
  set_sleep_mode(SLEEP_MODE_PWR_DOWN);
  sleep_enable();
  PORTB &= ~(1 << RF_PIN);
  sleep_mode();
  sleep_disable();
}

// ---------------------------------------------------------------------------
// SETUP / LOOP
// ---------------------------------------------------------------------------
void setup() {
  pinMode(RF_PIN, OUTPUT);
  digitalWrite(RF_PIN, LOW);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LED_OFF);

  aht20_init_sensor();
  setup_watchdog();
}

// Helper to delay without WDT timeout/overlap
void safe_delay(unsigned long ms) {
  unsigned long start = millis();
  while (millis() - start < ms) {
    wdt_reset();
  }
}

void loop() {
  // Lógica Adaptativa por Canal (Universal):
  // Selección automática de estrategia de ahorro según el canal.
  
  uint8_t target_wdt_cycles = 10;
  unsigned long active_delay_ms = 0;

  switch (g_channel) {
    case 1: // Canal 1 -> Target 39s
       // 9 ciclos WDT (~38s) + 1000ms delay = 39s
       target_wdt_cycles = 9;
       active_delay_ms = 1000;
       break;

    case 2: // Canal 2 -> Target 41s
       // 9 ciclos WDT (~38s) + 3000ms delay = 41s
       target_wdt_cycles = 9;
       active_delay_ms = 3000;
       break;

    case 4: // Canal 3 -> Target 43s
       // 10 ciclos WDT (~42.2s) + 800ms delay = 43s
       // (Ajuste fino para asegurar los 43s exactos si 10 ciclos se quedan cortos)
       // NOTA: Pruebas indicaron 10 ciclos = 43s.
       target_wdt_cycles = 10;
       active_delay_ms = 800; 
       break;

    default: // Por defecto (Conservador, Ch3)
       target_wdt_cycles = 10;
       active_delay_ms = 0;
       break;
  }

  if (wdt_cycles >= target_wdt_cycles) {
    wdt_cycles = 0;

    float tempC = 0.0f;
    static float last_valid_temp = 0.0f;

    bool success = aht20_read(tempC);
    if (!success) {
      delay(50);
      aht20_init_sensor();
      delay(50);
      success = aht20_read(tempC);
    }

    if (success) {
      tempC = roundf(tempC * 10.0f) / 10.0f;
      last_valid_temp = tempC;
    } else {
      pinMode(LED_PIN, OUTPUT);
      for (int i = 0; i < 5; i++) {
        digitalWrite(LED_PIN, LED_ON);  delay(100);
        digitalWrite(LED_PIN, LED_OFF); delay(100);
      }
      tempC = last_valid_temp;
    }

    uint8_t ec40[8];
    build_ec40_post(tempC, g_channel, g_device_id, ec40);
    
    // Retardo activo solo si es necesario para cuadrar el intervalo
    // IMPORTANTE: safe_delay resetea el WDT para evitar reinicios
    if (active_delay_ms > 0) {
       safe_delay(active_delay_ms);
    }
    
    sendOregonFrame(ec40);
  }

  enter_sleep();
}
