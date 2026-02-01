// ==================== MQTT Discovery simplificado ====================

void publicarDiscoveryMQTT() {
  Serial.println("\n--- Publicando MQTT Discovery ---");

  if (!mqttClient.connected()) {
    Serial.println("ERROR: MQTT no conectado");
    return;
  }

  // Device info común (simplificado)
  String dev = "\"dev\":{\"ids\":[\"" + String(MQTT_CLIENT_ID) + "\"],\"name\":\"" + String(DEVICE_NAME) + "\"}";

  // 1. Sensor PESO
  String c1 = "{\"name\":\"Peso\",\"uniq_id\":\"" + String(MQTT_CLIENT_ID) + "_w\",";
  c1 += "\"stat_t\":\"" + String(MQTT_TOPIC) + "\",";
  c1 += "\"val_tpl\":\"{{value_json.weight}}\",\"unit_of_meas\":\"g\",\"dev_cla\":\"weight\",\"stat_cla\":\"measurement\"," + dev + "}";
  
  Serial.printf("Peso size: %d bytes\n", c1.length());
  bool r1 = mqttPublishRetained("homeassistant/sensor/esp32feeder/weight/config", c1.c_str(), true);
  Serial.println(r1 ? "✓ Peso" : "✗ Peso");
  delay(200);

  // 2. Binary Sensor ESTABLE
  String c2 = "{\"name\":\"Estable\",\"uniq_id\":\"" + String(MQTT_CLIENT_ID) + "_s\",";
  c2 += "\"stat_t\":\"" + String(MQTT_TOPIC) + "\",";
  c2 += "\"val_tpl\":\"{{ 'true' if value_json.stable else 'false' }}\",\"pl_on\":\"true\",\"pl_off\":\"false\"," + dev + "}";
  
  Serial.printf("Estable size: %d bytes\n", c2.length());
  bool r2 = mqttPublishRetained("homeassistant/binary_sensor/esp32feeder/stable/config", c2.c_str(), true);
  Serial.println(r2 ? "✓ Estable" : "✗ Estable");
  delay(200);

  // 3. Sensor DESVIACIÓN
  String c3 = "{\"name\":\"Desviación\",\"uniq_id\":\"" + String(MQTT_CLIENT_ID) + "_d\",";
  c3 += "\"stat_t\":\"" + String(MQTT_TOPIC) + "\",";
  c3 += "\"val_tpl\":\"{{value_json.std_dev}}\",\"unit_of_meas\":\"g\",\"ent_cat\":\"diagnostic\"," + dev + "}";
  
  Serial.printf("Desviación size: %d bytes\n", c3.length());
  bool r3 = mqttPublishRetained("homeassistant/sensor/esp32feeder/stddev/config", c3.c_str(), true);
  Serial.println(r3 ? "✓ Desviación" : "✗ Desviación");
  delay(200);

  // 4. Sensor RSSI
  String c4 = "{\"name\":\"WiFi\",\"uniq_id\":\"" + String(MQTT_CLIENT_ID) + "_r\",";
  c4 += "\"stat_t\":\"" + String(MQTT_TOPIC) + "\",";
  c4 += "\"val_tpl\":\"{{value_json.rssi}}\",\"unit_of_meas\":\"dBm\",\"dev_cla\":\"signal_strength\",\"ent_cat\":\"diagnostic\"," + dev + "}";
  
  Serial.printf("WiFi size: %d bytes\n", c4.length());
  bool r4 = mqttPublishRetained("homeassistant/sensor/esp32feeder/rssi/config", c4.c_str(), true);
  Serial.println(r4 ? "✓ WiFi" : "✗ WiFi");
  delay(200);

  // 5. Sensor BOOT
  String c5 = "{\"name\":\"Boot\",\"uniq_id\":\"" + String(MQTT_CLIENT_ID) + "_b\",";
  c5 += "\"stat_t\":\"" + String(MQTT_TOPIC) + "\",";
  c5 += "\"val_tpl\":\"{{value_json.boot_count}}\",\"stat_cla\":\"total_increasing\",\"ent_cat\":\"diagnostic\"," + dev + "}";
  
  Serial.printf("Boot size: %d bytes\n", c5.length());
  bool r5 = mqttPublishRetained("homeassistant/sensor/esp32feeder/boot/config", c5.c_str(), true);
  Serial.println(r5 ? "✓ Boot" : "✗ Boot");
  delay(200);

  Serial.println("Discovery completado!");
  
  // Asegurar envío
  for (int i = 0; i < 10; i++) { 
    mqttClient.loop(); 
    delay(30); 
  }
}
