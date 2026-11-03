#include <HardwareSerial.h>

// =====================================================
// ESP32 DUAL RYLR896 ALTERNATING COUNTER / ALPHABET
// =====================================================

HardwareSerial LoRa1(2); // UART2: RX=16, TX=17
HardwareSerial LoRa2(1); // UART1: RX=25, TX=26

#define LORA1_RX 16
#define LORA1_TX 17
#define LORA2_RX 25
#define LORA2_TX 26

#define LORA_BAUD 115200

#define MODULE1_ADDRESS 101
#define MODULE2_ADDRESS 102
#define NETWORK_ID 6
#define RF_FREQUENCY 868000000UL

// State machine variables
int counter1 = 0;
char alphabetChar = 'A';
bool m1Turn = true; // True = Module 1 sends counter, False = Module 2 replies with alphabet

unsigned long lastActionTime = 0;
const unsigned long INTERVAL = 3000; // 3 seconds per turn

String readResponse(HardwareSerial &radio, unsigned long timeout) {
  String response = "";
  unsigned long start = millis();
  while (millis() - start < timeout) {
    while (radio.available()) {
      response += (char)radio.read();
    }
    delay(2);
  }
  response.trim();
  return response;
}

bool sendAT(HardwareSerial &radio, const char *command, const char *expected, const char *moduleName) {
  while (radio.available()) radio.read();
  radio.println(command);
  String response = readResponse(radio, 1500);
  return response.indexOf(expected) >= 0;
}

bool configureModule(HardwareSerial &radio, int address, const char *moduleName) {
  if (!sendAT(radio, "AT", "+OK", moduleName)) return false;

  char cmd[50];
  snprintf(cmd, sizeof(cmd), "AT+ADDRESS=%d", address);
  if (!sendAT(radio, cmd, "+OK", moduleName)) return false;

  snprintf(cmd, sizeof(cmd), "AT+NETWORKID=%d", NETWORK_ID);
  if (!sendAT(radio, cmd, "+OK", moduleName)) return false;

  snprintf(cmd, sizeof(cmd), "AT+BAND=%lu", RF_FREQUENCY);
  if (!sendAT(radio, cmd, "+OK", moduleName)) return false;

  if (!sendAT(radio, "AT+PARAMETER=7,9,1,4", "+OK", moduleName)) return false;
  
  // Fixed typo here: exactly 4 arguments now passed to sendAT
  if (!sendAT(radio, "AT+CRFOP=2", "+OK", moduleName)) {
    sendAT(radio, "AT+CRFOP=2", "+OK", moduleName);
  }

  return true;
}

void pollRadio(HardwareSerial &radio, const char *moduleName) {
  while (radio.available()) {
    String line = radio.readStringUntil('\n');
    line.trim();
    if (line.length() > 0) {
      if (line.startsWith("+RCV=")) {
        int firstComma = line.indexOf(',');
        int secondComma = line.indexOf(',', firstComma + 1);
        if (firstComma > 0 && secondComma > 0) {
          String sender = line.substring(5, firstComma);
          int lastComma = line.lastIndexOf(',');
          int secondLastComma = line.lastIndexOf(',', lastComma - 1);
          String payload = line.substring(secondComma + 1, secondLastComma);
          String rssi = line.substring(secondLastComma + 1, lastComma);
          
          Serial.println("==================================================");
          Serial.printf(" [SUCCESS] %s HEARD OVER-THE-AIR!\n", moduleName);
          Serial.printf("   ├── From Node : %s\n", sender.c_str());
          Serial.printf("   ├── Payload   : \"%s\"\n", payload.c_str());
          Serial.printf("   └── RSSI      : %s dBm\n", rssi.c_str());
          Serial.println("==================================================");
        }
      } else {
        Serial.printf("[ESP32] [%s] %s\n", moduleName, line.c_str());
      }
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(1500);

  Serial.println("\nInitializing Dual LoRa Modules (Counter/Alphabet Mode)...");
  LoRa1.begin(LORA_BAUD, SERIAL_8N1, LORA1_RX, LORA1_TX);
  LoRa2.begin(LORA_BAUD, SERIAL_8N1, LORA2_RX, LORA2_TX);
  delay(1000);

  if (!configureModule(LoRa1, MODULE1_ADDRESS, "MODULE 1") || 
      !configureModule(LoRa2, MODULE2_ADDRESS, "MODULE 2")) {
    Serial.println("[FAIL] Setup configuration failed.");
    while (true) delay(1000);
  }

  Serial.println("[READY] Modules configured. Starting alternating ping-pong dialogue...\n");
}

void loop() {
  pollRadio(LoRa1, "MODULE 1");
  pollRadio(LoRa2, "MODULE 2");

  unsigned long now = millis();
  if (now - lastActionTime >= INTERVAL) {
    lastActionTime = now;

    if (m1Turn) {
      counter1++;
      char msg[30];
      snprintf(msg, sizeof(msg), "Count: %d", counter1);
      
      Serial.printf("[DIALOGUE] Module 1 -> Module 2 | %s\n", msg);
      LoRa1.printf("AT+SEND=%d,%d,%s\r\n", MODULE2_ADDRESS, strlen(msg), msg);
    } else {
      char msg[30];
      snprintf(msg, sizeof(msg), "Alphabet: %c", alphabetChar);
      
      Serial.printf("[DIALOGUE] Module 2 -> Module 1 | %s\n", msg);
      LoRa2.printf("AT+SEND=%d,%d,%s\r\n", MODULE1_ADDRESS, strlen(msg), msg);

      alphabetChar++;
      if (alphabetChar > 'Z') alphabetChar = 'A';
    }

    m1Turn = !m1Turn;
  }
}
