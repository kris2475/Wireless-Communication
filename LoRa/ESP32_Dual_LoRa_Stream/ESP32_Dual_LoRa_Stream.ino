#include <HardwareSerial.h>

HardwareSerial LoRa1(2); // UART2
HardwareSerial LoRa2(1); // UART1

#define LORA1_RX 16
#define LORA1_TX 17
#define LORA2_RX 25
#define LORA2_TX 26
#define LORA_BAUD 115200

// Default parameters
int addr1 = 101;
int addr2 = 102;
int netId = 6;
unsigned long band = 868000000UL;
int rfPower = 2; // Default 2 dBm

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

void applyModuleSettings(int a1, int a2, int nId, unsigned long bnd, int pwr) {
  addr1 = a1;
  addr2 = a2;
  netId = nId;
  band = bnd;
  rfPower = pwr;

  char cmd[50];

  // Configure Module 1
  sendAT(LoRa1, "AT", "+OK", "MODULE 1");
  snprintf(cmd, sizeof(cmd), "AT+ADDRESS=%d", addr1);
  sendAT(LoRa1, cmd, "+OK", "MODULE 1");
  snprintf(cmd, sizeof(cmd), "AT+NETWORKID=%d", netId);
  sendAT(LoRa1, cmd, "+OK", "MODULE 1");
  snprintf(cmd, sizeof(cmd), "AT+BAND=%lu", band);
  sendAT(LoRa1, cmd, "+OK", "MODULE 1");
  snprintf(cmd, sizeof(cmd), "AT+CRFOP=%d", rfPower);
  sendAT(LoRa1, cmd, "+OK", "MODULE 1");

  // Configure Module 2
  sendAT(LoRa2, "AT", "+OK", "MODULE 2");
  snprintf(cmd, sizeof(cmd), "AT+ADDRESS=%d", addr2);
  sendAT(LoRa2, cmd, "+OK", "MODULE 2");
  snprintf(cmd, sizeof(cmd), "AT+NETWORKID=%d", netId);
  sendAT(LoRa2, cmd, "+OK", "MODULE 2");
  snprintf(cmd, sizeof(cmd), "AT+BAND=%lu", band);
  sendAT(LoRa2, cmd, "+OK", "MODULE 2");
  snprintf(cmd, sizeof(cmd), "AT+CRFOP=%d", rfPower);
  sendAT(LoRa2, cmd, "+OK", "MODULE 2");

  Serial.println("[CONFIG_APPLIED] Modules successfully updated with live parameters.");
}

void pollRadios() {
  for (int i = 1; i <= 2; i++) {
    HardwareSerial &radio = (i == 1) ? LoRa1 : LoRa2;
    const char *modName = (i == 1) ? "MODULE 1" : "MODULE 2";
    
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
            
            Serial.printf("[RX_EVENT] Target:%s | From:%s | Payload:\"%s\" | RSSI:%s dBm\n", 
                          modName, sender.c_str(), payload.c_str(), rssi.c_str());
          }
        } else {
          Serial.printf("[ESP32] [%s] %s\n", modName, line.c_str());
        }
      }
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  Serial.println("\nInitializing Dual LoRa Controller...");
  
  LoRa1.begin(LORA_BAUD, SERIAL_8N1, LORA1_RX, LORA1_TX);
  LoRa2.begin(LORA_BAUD, SERIAL_8N1, LORA2_RX, LORA2_TX);
  delay(1000);

  applyModuleSettings(addr1, addr2, netId, band, rfPower);
}

void loop() {
  pollRadios();

  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.length() > 0) {
      if (cmd.startsWith("CONFIG:")) {
        // Format: CONFIG:m1Addr,m2Addr,netId,band,power
        int c1 = cmd.indexOf(',');
        int c2 = cmd.indexOf(',', c1 + 1);
        int c3 = cmd.indexOf(',', c2 + 1);
        int c4 = cmd.indexOf(',', c3 + 1);
        if (c1 > 0 && c2 > 0 && c3 > 0 && c4 > 0) {
          int newA1 = cmd.substring(7, c1).toInt();
          int newA2 = cmd.substring(c1 + 1, c2).toInt();
          int newNet = cmd.substring(c2 + 1, c3).toInt();
          unsigned long newBand = cmd.substring(c3 + 1, c4).toInt();
          int newPwr = cmd.substring(c4 + 1).toInt();
          
          applyModuleSettings(newA1, newA2, newNet, newBand, newPwr);
        }
      } else if (cmd.startsWith("SEND1:")) {
        int comma = cmd.indexOf(',', 6);
        if (comma > 0) {
          int dest = cmd.substring(6, comma).toInt();
          String msg = cmd.substring(comma + 1);
          LoRa1.printf("AT+SEND=%d,%d,%s\r\n", dest, msg.length(), msg.c_str());
          Serial.printf("[TX_CONFIRM] Module 1 sent to %d: %s\n", dest, msg.c_str());
        }
      } else if (cmd.startsWith("SEND2:")) {
        int comma = cmd.indexOf(',', 6);
        if (comma > 0) {
          int dest = cmd.substring(6, comma).toInt();
          String msg = cmd.substring(comma + 1);
          LoRa2.printf("AT+SEND=%d,%d,%s\r\n", dest, msg.length(), msg.c_str());
          Serial.printf("[TX_CONFIRM] Module 2 sent to %d: %s\n", dest, msg.c_str());
        }
      }
    }
  }
}
