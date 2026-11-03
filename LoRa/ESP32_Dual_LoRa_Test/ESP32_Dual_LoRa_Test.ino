#include <HardwareSerial.h>

// =====================================================
// ESP32 DUAL RYLR896 COMMUNICATION
// =====================================================

// Module 1: Address 101
// UART2: GPIO16 RX, GPIO17 TX
HardwareSerial LoRa1(2);

// Module 2: Address 102
// UART1: GPIO25 RX, GPIO26 TX
HardwareSerial LoRa2(1);

#define LORA1_RX 16
#define LORA1_TX 17

#define LORA2_RX 25
#define LORA2_TX 26

#define LORA_BAUD 115200

#define MODULE1_ADDRESS 101
#define MODULE2_ADDRESS 102
#define NETWORK_ID 6

unsigned long lastSend1 = 0;
unsigned long lastSend2 = 0;

const unsigned long SEND_INTERVAL = 4000;

// =====================================================
// READ MODULE RESPONSE
// =====================================================

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

// =====================================================
// SEND AT COMMAND
// =====================================================

bool sendAT(HardwareSerial &radio, const char *command,
            const char *expected, const char *moduleName) {

  while (radio.available()) radio.read();

  Serial.printf("[%s] TX: %s\n", moduleName, command);

  radio.println(command);

  String response = readResponse(radio, 1500);

  Serial.printf("[%s] RX: %s\n",
                moduleName,
                response.length() ? response.c_str() : "<NO RESPONSE>");

  return response.indexOf(expected) >= 0;
}

// =====================================================
// CONFIGURE MODULE
// =====================================================

bool configureModule(HardwareSerial &radio,
                     int address,
                     const char *moduleName) {

  Serial.printf("\n========== %s ==========\n", moduleName);

  if (!sendAT(radio, "AT", "+OK", moduleName)) {
    Serial.println("[FAIL] UART communication");
    return false;
  }

  char command[40];

  snprintf(command, sizeof(command), "AT+ADDRESS=%d", address);

  if (!sendAT(radio, command, "+OK", moduleName)) {
    Serial.println("[FAIL] Address configuration");
    return false;
  }

  if (!sendAT(radio, "AT+ADDRESS?", "+ADDRESS=", moduleName)) {
    Serial.println("[FAIL] Address readback");
    return false;
  }

  snprintf(command, sizeof(command), "AT+NETWORKID=%d", NETWORK_ID);

  if (!sendAT(radio, command, "+OK", moduleName)) {
    Serial.println("[FAIL] Network configuration");
    return false;
  }

  if (!sendAT(radio, "AT+NETWORKID?", "+NETWORKID=6", moduleName)) {
    Serial.println("[FAIL] Network readback");
    return false;
  }

  if (!sendAT(radio, "AT+IPR?", "+IPR=115200", moduleName)) {
    Serial.println("[FAIL] Baud verification");
    return false;
  }

  Serial.printf("[PASS] %s READY\n", moduleName);
  return true;
}

// =====================================================
// RECEIVE RADIO DATA
// =====================================================

void receiveData(HardwareSerial &radio, const char *moduleName) {

  while (radio.available()) {
    String message = radio.readStringUntil('\n');
    message.trim();

    if (message.length()) {
      Serial.printf("[%s] RECEIVED: %s\n",
                    moduleName, message.c_str());
    }
  }
}

// =====================================================
// TRANSMIT RADIO DATA
// =====================================================

void transmitData(HardwareSerial &radio,
                  int destination,
                  const char *message,
                  const char *moduleName) {

  char command[120];

  snprintf(command, sizeof(command),
           "AT+SEND=%d,%d,%s",
           destination,
           strlen(message),
           message);

  Serial.printf("[%s] TX: %s\n", moduleName, command);

  radio.println(command);
}

// =====================================================
// SETUP
// =====================================================

void setup() {

  Serial.begin(115200);
  delay(1500);

  Serial.println();
  Serial.println("====================================");
  Serial.println(" ESP32 DUAL RYLR896 COMMUNICATION");
  Serial.println("====================================");

  Serial.println();
  Serial.println("UART CONFIGURATION:");
  Serial.println("Module 1: UART2 | RX=16 | TX=17");
  Serial.println("Module 2: UART1 | RX=25 | TX=26");
  Serial.println("UART baud: 115200");

  LoRa1.begin(LORA_BAUD, SERIAL_8N1, LORA1_RX, LORA1_TX);
  LoRa2.begin(LORA_BAUD, SERIAL_8N1, LORA2_RX, LORA2_TX);

  LoRa1.setTimeout(50);
  LoRa2.setTimeout(50);

  delay(1000);

  bool module1Ready = configureModule(
    LoRa1, MODULE1_ADDRESS, "MODULE 1");

  bool module2Ready = configureModule(
    LoRa2, MODULE2_ADDRESS, "MODULE 2");

  Serial.println();
  Serial.println("========== STARTUP SUMMARY ==========");

  Serial.printf("Module 1 (101): %s\n",
                module1Ready ? "PASS" : "FAIL");

  Serial.printf("Module 2 (102): %s\n",
                module2Ready ? "PASS" : "FAIL");

  if (module1Ready && module2Ready) {
    Serial.println("[PASS] BOTH MODULES READY");
    Serial.println("[INFO] Bidirectional transmission enabled");
  } else {
    Serial.println("[FAIL] CONFIGURATION INCOMPLETE");
    Serial.println("[HALT] Communications disabled");
  }

  if (!module1Ready || !module2Ready) {
    while (true) delay(1000);
  }
}

// =====================================================
// MAIN LOOP
// =====================================================

void loop() {

  receiveData(LoRa1, "MODULE 1");
  receiveData(LoRa2, "MODULE 2");

  unsigned long now = millis();

  if (now - lastSend1 >= SEND_INTERVAL) {
    lastSend1 = now;
    transmitData(
      LoRa1,
      MODULE2_ADDRESS,
      "Hello from 101",
      "MODULE 1"
    );
  }

  if (now - lastSend2 >= SEND_INTERVAL) {
    lastSend2 = now;
    transmitData(
      LoRa2,
      MODULE1_ADDRESS,
      "Hello back from 102",
      "MODULE 2"
    );
  }
}
