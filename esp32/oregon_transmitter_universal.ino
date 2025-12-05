/*
 * Oregon Scientific THN132N (EC40) - VERSIÓ UNIVERSAL
 * Generador amb taules universals descobertes
 * 
 * DESCOBRIMENTS IMPLEMENTATS:
 * - R1 i M: Fórmula universal (suma de nibbles)
 * - P: LUT optimitzada + transformacions XOR
 * - Nibble 7: Rolling code configurable
 * 
 * Basat en la investigació exhaustiva documentada a:
 * ec40_lut_suite/04_universal_mp_analysis/Docs/
 */

#include <Arduino.h>
#include <math.h>
#include "driver/rmt.h"
#include "driver/gpio.h"
#include <OneWire.h>
#include <DallasTemperature.h>

// ---------------------------------------------------------------------------
// CONFIGURACIÓ HW
// ---------------------------------------------------------------------------

#define TX_GPIO      GPIO_NUM_4
#define RMT_CH       RMT_CHANNEL_0
#define T_UNIT       488  // µs per semibit
#define ONE_WIRE_BUS GPIO_NUM_5

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// Paràmetres de configuració
static uint8_t CHANNEL    = 1;      // 1..3
static uint8_t DEVICE_ID  = 247;    // House Code (0-255)
static uint8_t ROLLING_CODE = 0x2;  // Rolling code (0, 1, 2, o 8)

// ---------------------------------------------------------------------------
// TAULA DE TRANSFORMACIONS XOR PER ROLLING CODE
// ---------------------------------------------------------------------------
// Descobriment: P(nib7) = P(nib7_base) XOR NIB7_XOR
// Base: Nib7 = 0x2

const uint8_t NIB7_XOR_TABLE[16] = {
  0x6, // 0x0: P(0) = P(2) XOR 0x6
  0xD, // 0x1: P(1) = P(2) XOR 0xD
  0x0, // 0x2: P(2) = P(2) (base)
  0x0, 0x0, 0x0, 0x0, 0x0, // 0x3-0x7: No usats
  0x7, // 0x8: P(8) = P(2) XOR 0x7
  0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0  // 0x9-0xF: No usats
};

// ---------------------------------------------------------------------------
// LUT DE P (Base per Nib7=0x2, House 247)
// 405 punts: -16.0°C a +61.4°C
// ---------------------------------------------------------------------------
// Índex: temp_idx = (int)round((temp_c + 40) * 10)

struct P_LUT_Entry {
  int16_t temp_idx;
  uint8_t p_value;
};

// LUT compacta (només punts capturats)
const P_LUT_Entry P_LUT_BASE[] PROGMEM = {
  {240, 0xA}, {241, 0x4}, {242, 0x3}, {243, 0x7}, {244, 0x0}, 
  {245, 0x9}, {246, 0xE}, {247, 0xC}, {248, 0xB}, {249, 0x2},
  {250, 0x5}, {251, 0x1}, {252, 0x6}, {253, 0x2}, {254, 0x5},
  {255, 0xC}, {256, 0xB}, {257, 0x9}, {258, 0xE}, {259, 0x7},
  {260, 0x0}, {261, 0xA}, {262, 0xD}, {263, 0x9}, {264, 0xE},
  {265, 0x7}, {266, 0x0}, {268, 0x5}, {269, 0xC}, {270, 0xB},
  {271, 0xF}, {272, 0x8}, {273, 0xC}, {274, 0xB}, {275, 0x2},
  {276, 0x5}, {277, 0x7}, {278, 0x0}, {279, 0x9}, {280, 0xE},
  {281, 0x0}, {282, 0x7}, {283, 0x3}, {284, 0x4}, {285, 0xD},
  {286, 0xA}, {288, 0xF}, {289, 0x6}, {290, 0x1}, {291, 0x5},
  {292, 0x2}, {293, 0x6}, {295, 0x8}, {297, 0xD}, {298, 0xA},
  {299, 0x3}, {300, 0x4}, {301, 0x8}, {303, 0xB}, {304, 0xC},
  {306, 0x2}, {307, 0x0}, {308, 0x7}, {309, 0xE}, {310, 0x9},
  {311, 0xD}, {312, 0xA}, {313, 0xE}, {314, 0x9}, {315, 0x0},
  {316, 0x7}, {317, 0x5}, {319, 0xB}, {320, 0xC}, {321, 0xE},
  {322, 0x9}, {324, 0xA}, {325, 0x3}, {326, 0x4}, {328, 0x1},
  {329, 0x8}, {330, 0xF}, {331, 0xB}, {332, 0xC}, {333, 0x8},
  {334, 0xF}, {335, 0x6}, {336, 0x1}, {338, 0x4}, {340, 0xA},
  {341, 0x4}, {342, 0x3}, {343, 0x7}, {344, 0x0}, {346, 0xE},
  {347, 0xC}, {349, 0x2}, {350, 0x5}, {352, 0x6}, {354, 0x5},
  {355, 0xC}, {356, 0xB}, {357, 0x9}, {359, 0x7}, {360, 0x0},
  {361, 0xA}, {362, 0xD}, {363, 0x9}, {364, 0xE}, {365, 0x7},
  {367, 0x2}, {368, 0x5}, {369, 0xC}, {371, 0xF}, {373, 0xC},
  {374, 0xB}, {376, 0x5}, {378, 0x0}, {379, 0x9}, {380, 0xE},
  {381, 0x0}, {383, 0x3}, {385, 0xD}, {387, 0x8}, {390, 0x1},
  {392, 0x2}, {394, 0x1}, {396, 0xF}, {398, 0xA}, {400, 0x4},
  {401, 0xB}, {402, 0x2}, {403, 0x5}, {404, 0x7}, {406, 0x9},
  {408, 0xA}, {410, 0x9}, {412, 0x7}, {413, 0x0}, {414, 0x2},
  {416, 0xC}, {417, 0xB}, {418, 0xF}, {419, 0x8}, {420, 0x6},
  {421, 0x1}, {422, 0x8}, {423, 0xF}, {425, 0xA}, {427, 0x4},
  {428, 0x0}, {429, 0x7}, {430, 0x3}, {431, 0x4}, {432, 0xD},
  {433, 0xA}, {434, 0x8}, {435, 0xF}, {437, 0x1}, {438, 0x5},
  {439, 0x2}, {440, 0x8}, {441, 0xF}, {442, 0x6}, {444, 0x3},
  {446, 0xD}, {447, 0xA}, {448, 0xE}, {449, 0x9}, {450, 0xD},
  {451, 0xA}, {452, 0x3}, {453, 0x4}, {454, 0x6}, {455, 0x1},
  {456, 0x8}, {458, 0xB}, {459, 0xC}, {461, 0x5}, {462, 0xC},
  {463, 0xB}, {464, 0x9}, {465, 0xE}, {466, 0x7}, {468, 0x4},
  {469, 0x3}, {471, 0x0}, {472, 0x9}, {473, 0xE}, {474, 0xC},
  {475, 0xB}, {476, 0x2}, {477, 0x5}, {478, 0x1}, {479, 0x6},
  {480, 0x4}, {481, 0x3}, {482, 0xA}, {484, 0xF}, {485, 0x8},
  {486, 0x1}, {488, 0x2}, {489, 0x5}, {490, 0x1}, {491, 0x6},
  {493, 0x8}, {495, 0xD}, {496, 0x4}, {497, 0x3}, {498, 0x7},
  {499, 0x0}, {500, 0xC}, {501, 0xB}, {502, 0x2}, {503, 0x5},
  {504, 0x7}, {505, 0x0}, {506, 0x9}, {507, 0xE}, {508, 0xA},
  {509, 0xD}, {510, 0x9}, {511, 0xE}, {512, 0x7}, {513, 0x0},
  {514, 0x2}, {515, 0x5}, {516, 0xC}, {517, 0xB}, {518, 0xF},
  {519, 0x8}, {520, 0x6}, {521, 0x1}, {522, 0x8}, {523, 0xF},
  {524, 0xD}, {525, 0xA}, {526, 0x3}, {527, 0x4}, {528, 0x0},
  {529, 0x7}, {530, 0x3}, {531, 0x4}, {532, 0xD}, {533, 0xA},
  {534, 0x8}, {535, 0xF}, {536, 0x6}, {537, 0x1}, {538, 0x5},
  {539, 0x2}, {540, 0x8}, {541, 0xF}, {542, 0x6}, {543, 0x1},
  {544, 0x3}, {545, 0x4}, {546, 0xD}, {547, 0xA}, {548, 0xE},
  {549, 0x9}, {550, 0xD}, {551, 0xA}, {552, 0x3}, {553, 0x4},
  {554, 0x6}, {555, 0x1}, {556, 0x8}, {557, 0xF}, {558, 0xB},
  {559, 0xC}, {560, 0x2}, {561, 0x5}, {562, 0xC}, {563, 0xB},
  {564, 0x9}, {565, 0xE}, {566, 0x7}, {567, 0x0}, {568, 0x4},
  {569, 0x3}, {570, 0x7}, {571, 0x0}, {572, 0x9}, {573, 0xE},
  {574, 0xC}, {575, 0xB}, {576, 0x2}, {577, 0x5}, {578, 0x1},
  {579, 0x6}, {580, 0x4}, {581, 0x3}, {582, 0xA}, {583, 0xD},
  {584, 0xF}, {585, 0x8}, {586, 0x1}, {588, 0x2}, {589, 0x5},
  {591, 0x6}, {592, 0xF}, {593, 0x8}, {595, 0xD}, {596, 0x4},
  {597, 0x3}, {598, 0x7}, {599, 0x0}, {600, 0xC}, {601, 0xB},
  {602, 0x2}, {603, 0x5}, {604, 0x7}, {605, 0x0}, {606, 0x9},
  {607, 0xE}, {608, 0xA}, {609, 0xD}, {610, 0x9}, {611, 0xE},
  {612, 0x7}, {613, 0x0}, {614, 0x2}, {615, 0x5}, {616, 0xC},
  {617, 0xB}, {618, 0xF}, {619, 0x8}, {620, 0x6}, {621, 0x1},
  {622, 0x8}, {623, 0xF}, {625, 0xA}, {626, 0x3}, {627, 0x4},
  {629, 0x7}, {631, 0x4}, {632, 0xD}, {633, 0xA}, {634, 0x8},
  {636, 0x6}, {637, 0x1}, {639, 0x2}, {640, 0x8}, {641, 0xF},
  {642, 0x6}, {643, 0x1}, {644, 0x3}, {645, 0x4}, {646, 0xD},
  {647, 0xA}, {649, 0x9}, {651, 0xA}, {652, 0x3}, {653, 0x4},
  {654, 0x6}, {656, 0x8}, {657, 0xF}, {658, 0xB}, {659, 0xC},
  {660, 0x2}, {661, 0x5}, {662, 0xC}, {663, 0xB}, {665, 0xE},
  {666, 0x7}, {667, 0x0}, {668, 0x4}, {670, 0x7}, {671, 0x0},
  {672, 0x9}, {676, 0x2}, {680, 0x4}, {686, 0x1}, {692, 0xF},
  {699, 0x0}, {707, 0xE}, {717, 0xB}, {728, 0x0}, {740, 0x8},
  {746, 0xD}, {753, 0x4}, {769, 0x3}, {786, 0x1}, {807, 0x9},
  {813, 0x7}, {815, 0x2}, {830, 0x4}, {834, 0xF}, {859, 0xB},
  {866, 0x0}, {873, 0x9}, {889, 0x2}, {896, 0x3}, {902, 0x5},
  {910, 0xE}, {915, 0x2}, {926, 0x4}, {931, 0x3}, {965, 0x9},
  {970, 0x0}, {971, 0x7}, {979, 0x1}, {986, 0x6}, {1014, 0x5}
};

const int P_LUT_SIZE = sizeof(P_LUT_BASE) / sizeof(P_LUT_Entry);

// ---------------------------------------------------------------------------
// FUNCIONS UNIVERSALS DESCOBERTES
// ---------------------------------------------------------------------------

uint8_t get_p_from_lut(float temp_celsius, uint8_t nib7) {
  // Calcular índex de temperatura
  int16_t temp_idx = (int16_t)round((temp_celsius + 40.0) * 10.0);
  
  // Buscar valor més proper a la LUT
  int16_t min_diff = 32767;
  uint8_t p_base = 0;
  
  for (int i = 0; i < P_LUT_SIZE; i++) {
    P_LUT_Entry entry;
    memcpy_P(&entry, &P_LUT_BASE[i], sizeof(P_LUT_Entry));
    
    int16_t diff = abs(temp_idx - entry.temp_idx);
    if (diff < min_diff) {
      min_diff = diff;
      p_base = entry.p_value;
      
      // Si trobem exacte, sortir
      if (diff == 0) break;
    }
  }
  
  // Aplicar transformació XOR segons rolling code
  uint8_t xor_val = (nib7 < 16) ? NIB7_XOR_TABLE[nib7] : 0;
  return (p_base ^ xor_val) & 0xF;
}

void calculate_universal_checksum(const uint8_t nibbles[12], 
                                   float temp_celsius,
                                   uint8_t nib7,
                                   uint8_t &r1, uint8_t &m, uint8_t &p) {
  // R1 i M: Fórmula universal (suma de nibbles)
  uint16_t sum = 0;
  for (int i = 0; i < 12; i++) {
    sum += nibbles[i];
  }
  
  uint8_t checksum_byte = sum & 0xFF;
  r1 = checksum_byte & 0xF;        // Nibble baix
  m = (checksum_byte >> 4) & 0xF;  // Nibble alt
  
  // P: LUT + transformació XOR
  p = get_p_from_lut(temp_celsius, nib7);
}

// ---------------------------------------------------------------------------
// FUNCIONS RMT (sense canvis)
// ---------------------------------------------------------------------------

void hex_string_to_bits(const char* hex, uint8_t* bits, int& bitlen) {
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

void build_raw_ook_frame(const char* hexstr, rmt_item32_t* items, int& length) {
  uint8_t bits[512];
  int bitlen = 0;
  hex_string_to_bits(hexstr, bits, bitlen);

  int idx = 0;
  for (int i = 0; i < bitlen; i++) {
    if (bits[i]) {
      items[idx].level0    = 1;
      items[idx].duration0 = T_UNIT;
      items[idx].level1    = 0;
      items[idx].duration1 = T_UNIT;
    } else {
      items[idx].level0    = 0;
      items[idx].duration0 = T_UNIT;
      items[idx].level1    = 1;
      items[idx].duration1 = T_UNIT;
    }
    idx++;
  }
  length = idx;
}

void setup_rmt() {
  rmt_config_t config = RMT_DEFAULT_CONFIG_TX(TX_GPIO, RMT_CH);
  config.clk_div = 80;
  ESP_ERROR_CHECK(rmt_config(&config));
  ESP_ERROR_CHECK(rmt_driver_install(config.channel, 0, 0));
}

// ---------------------------------------------------------------------------
// GENERADOR DE PAYLOAD AMB TAULES UNIVERSALS
// ---------------------------------------------------------------------------

void build_payload_nibbles(float temp_c, uint8_t channel, uint8_t device_id, 
                           uint8_t nib7, uint8_t nibbles[15]) {
  // Posicions 0-3: ID del sensor (EC40)
  nibbles[0] = 0xE;
  nibbles[1] = 0xC;
  nibbles[2] = 0x4;
  nibbles[3] = 0x0;
  
  // Posició 4: Channel
  nibbles[4] = channel & 0xF;
  
  // Posicions 5-6: House Code (LSN, MSN)
  nibbles[5] = device_id & 0xF;
  nibbles[6] = (device_id >> 4) & 0xF;
  
  // Posició 7: Rolling code
  nibbles[7] = nib7 & 0xF;
  
  // Posicions 8-10: Temperatura BCD
  float temp_abs = fabs(temp_c);
  int temp_int = (int)round(temp_abs * 10.0);
  
  nibbles[8] = temp_int % 10;              // LSN
  nibbles[9] = (temp_int / 10) % 10;       // Mid
  nibbles[10] = (temp_int / 100) % 10;     // MSN
  
  // Posició 11: Flags
  uint8_t flags = (temp_c < 0) ? 0x8 : 0x0;
  nibbles[11] = flags;
  
  // Posicions 12-14: Checksum (R1, M, P)
  uint8_t r1, m, p;
  calculate_universal_checksum(nibbles, temp_c, nib7, r1, m, p);
  
  nibbles[12] = r1;
  nibbles[13] = m;
  nibbles[14] = p;
}

void nibbles_to_bytes(const uint8_t nibbles[15], uint8_t bytes[8]) {
  // Convertir 15 nibbles a 8 bytes (format EC40 post-reflect)
  bytes[0] = (nibbles[0] << 4) | nibbles[1];  // EC
  bytes[1] = (nibbles[2] << 4) | nibbles[3];  // 40
  bytes[2] = (nibbles[4] << 4) | nibbles[5];  // Channel + House_LSN
  bytes[3] = (nibbles[6] << 4) | nibbles[7];  // House_MSN + Rolling
  bytes[4] = (nibbles[8] << 4) | nibbles[9];  // Temp LSN + Mid
  bytes[5] = (nibbles[10] << 4) | nibbles[11]; // Temp MSN + Flags
  bytes[6] = (nibbles[12] << 4) | nibbles[13]; // R1 + M
  bytes[7] = (nibbles[14] << 4) | 0x0;         // P + postamble(0)
}

void reflect_nibbles(const uint8_t *in, uint8_t *out, size_t len) {
  for (size_t i = 0; i < len; ++i) {
    uint8_t b = in[i];
    out[i] = (uint8_t)(((b & 0x0F) << 4) | (b >> 4));
  }
}

void build_raw_from_payload(const uint8_t payload_bytes[8], char *out_hex) {
  uint8_t reflected[8];
  reflect_nibbles(payload_bytes, reflected, 8);

  const uint8_t header_bytes[5] = { 0x55, 0x55, 0x55, 0x55, 0x99 };
  
  uint8_t all_bits[168];
  int idx = 0;

  // Header
  for (int i = 0; i < 5; ++i) {
    uint8_t b = header_bytes[i];
    for (int bit = 7; bit >= 0; --bit) {
      all_bits[idx++] = (uint8_t)((b >> bit) & 0x01);
    }
  }

  // Data + Manchester
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

  // Bits to hex
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

void sendOregonFrame(float temp_c, uint8_t channel, uint8_t device_id, uint8_t nib7) {
  // Generar payload amb taules universals
  uint8_t nibbles[15];
  build_payload_nibbles(temp_c, channel, device_id, nib7, nibbles);
  
  uint8_t payload_bytes[8];
  nibbles_to_bytes(nibbles, payload_bytes);
  
  char raw_hex[43];
  build_raw_from_payload(payload_bytes, raw_hex);

  // Debug
  Serial.print(F("Temp: "));
  Serial.print(temp_c, 1);
  Serial.print(F("°C, CH: "));
  Serial.print(channel);
  Serial.print(F(", House: "));
  Serial.print(device_id);
  Serial.print(F(", Nib7: 0x"));
  Serial.println(nib7, HEX);
  
  Serial.print(F("Payload (15 nib): "));
  for (int i = 0; i < 15; i++) {
    Serial.print(nibbles[i], HEX);
  }
  Serial.println();
  
  Serial.print(F("EC40 bytes: "));
  for (int i = 0; i < 8; ++i) {
    if (payload_bytes[i] < 0x10) Serial.print('0');
    Serial.print(payload_bytes[i], HEX);
  }
  Serial.println();
  
  Serial.print(F("RAW HEX: "));
  Serial.println(raw_hex);

  // Transmetre
  rmt_item32_t items[512];
  int item_len = 0;
  build_raw_ook_frame(raw_hex, items, item_len);

  rmt_write_items(RMT_CH, items, item_len, true);
  delayMicroseconds(4096);
  rmt_write_items(RMT_CH, items, item_len, true);
}

// ---------------------------------------------------------------------------
// SETUP / LOOP
// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println();
  Serial.println(F("=============================================="));
  Serial.println(F("Oregon THN132N - VERSIÓ UNIVERSAL"));
  Serial.println(F("Amb taules universals descobertes"));
  Serial.println(F("=============================================="));
  
  sensors.begin();
  Serial.print(F("Sensors DS18B20: "));
  Serial.println(sensors.getDeviceCount());
  
  Serial.print(F("House ID: "));
  Serial.println(DEVICE_ID);
  Serial.print(F("Channel: "));
  Serial.println(CHANNEL);
  Serial.print(F("Rolling Code: 0x"));
  Serial.println(ROLLING_CODE, HEX);
  Serial.println();
  
  setup_rmt();
}

void loop() {
  static uint32_t lastSend = 0;
  const uint32_t periodMs = 40 * 1000UL;

  uint32_t now = millis();
  if (now - lastSend >= periodMs) {
    lastSend = now;

    sensors.requestTemperatures();
    float temp_c = sensors.getTempCByIndex(0);
    
    if (temp_c == DEVICE_DISCONNECTED_C) {
      Serial.println(F("Error: No s'ha pogut llegir el sensor"));
      return;
    }

    Serial.println();
    Serial.println(F("--- Transmissió ---"));
    sendOregonFrame(temp_c, CHANNEL, DEVICE_ID, ROLLING_CODE);
    Serial.println(F("-------------------"));
    Serial.println();
    
    // Opcional: Incrementar rolling code
    // ROLLING_CODE = (ROLLING_CODE == 0x8) ? 0x0 : ((ROLLING_CODE == 0x2) ? 0x8 : (ROLLING_CODE + 1));
  }
}
