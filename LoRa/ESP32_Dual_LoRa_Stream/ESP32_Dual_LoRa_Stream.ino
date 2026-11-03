
#include <HardwareSerial.h>

// =====================================================
// ESP32 DUAL RYLR896 - PC DASHBOARD INTERFACE
// =====================================================

// Module 1: UART2
HardwareSerial LoRa1(2);

// Module 2: UART1
HardwareSerial LoRa2(1);

// Hardware connections
#define LORA1_RX 16
#define LORA1_TX 17

#define LORA2_RX 25
#define LORA2_TX 26

#define LORA_BAUD 115200
#define USB_BAUD 115200

// Module configuration
int address1 = 101;
int address2 = 102;
int network1 = 6;
int network2 = 6;

// Serial input buffers
String usbBuffer;
String radioBuffer1;
String radioBuffer2;

unsigned long lastHeartbeat = 0;

// =====================================================
// OUTPUT TO PYTHON DASHBOARD
// =====================================================

void dashboardMessage(const String &message) {
  Serial.println(message);
}

void radioEvent(int module, const String &message) {
  dashboardMessage("LORA|" + String(module) + "|" + message);
}

// =====================================================
// SEND COMMAND TO RADIO
// =====================================================

void sendRadioCommand(int module, const String &command) {

  HardwareSerial *radio;

  if (module == 1) {
    radio = &LoRa1;
  } else {
    radio = &LoRa2;
  }

  dashboardMessage(
    "TXCMD|" + String(module) + "|" + command
  );

  radio->println(command);
}

// =====================================================
// READ RADIO UARTS WITHOUT BLOCKING
// =====================================================

void readRadio(HardwareSerial &radio,
               String &buffer,
               int module) {

  while (radio.available()) {

    char c = (char)radio.read();

    if (c == '\r') continue;

    if (c == '\n') {

      buffer.trim();

      if (buffer.length() > 0) {
        radioEvent(module, buffer);
      }

      buffer = "";
    }
    else if (buffer.length() < 500) {
      buffer += c;
    }
  }
}

// =====================================================
// PROCESS PC COMMANDS
// =====================================================

void processCommand(String command) {

  command.trim();

  if (command.length() == 0) return;

  // PING
  if (command == "PING") {
    dashboardMessage("PONG|ESP32_DUAL_RYLR896");
    return;
  }

  // QUERY,module,ADDRESS
  // QUERY,module,NETWORKID
  if (command.startsWith("QUERY,")) {

    int first = command.indexOf(',');
    int second = command.indexOf(',', first + 1);

    if (second < 0) return;

    int module = command.substring(first + 1, second).toInt();
    String parameter = command.substring(second + 1);

    if (module < 1 || module > 2) return;

    if (parameter == "ADDRESS") {
      sendRadioCommand(module, "AT+ADDRESS?");
    }
    else if (parameter == "NETWORKID") {
      sendRadioCommand(module, "AT+NETWORKID?");
    }
    else if (parameter == "IPR") {
      sendRadioCommand(module, "AT+IPR?");
    }

    return;
  }

  // CFG,module,ADDRESS,value
  // CFG,module,NETWORKID,value
  if (command.startsWith("CFG,")) {

    int first = command.indexOf(',');
    int second = command.indexOf(',', first + 1);
    int third = command.indexOf(',', second + 1);

    if (first < 0 || second < 0 || third < 0) return;

    int module = command.substring(first + 1, second).toInt();

    String parameter =
      command.substring(second + 1, third);

    String value =
      command.substring(third + 1);

    if (module < 1 || module > 2) return;

    int numericValue = value.toInt();

    if (parameter == "ADDRESS") {

      if (numericValue < 0 || numericValue > 65535) {
        dashboardMessage("ERROR|Invalid address");
        return;
      }

      if (module == 1) address1 = numericValue;
      else address2 = numericValue;

      sendRadioCommand(
        module,
        "AT+ADDRESS=" + String(numericValue)
      );
    }

    else if (parameter == "NETWORKID") {

      if (numericValue < 3 || numericValue > 15) {
        dashboardMessage("ERROR|Network ID must be 3-15");
        return;
      }

      if (module == 1) network1 = numericValue;
      else network2 = numericValue;

      sendRadioCommand(
        module,
        "AT+NETWORKID=" + String(numericValue)
      );
    }

    return;
  }

  // SEND,module,destination,payload
  if (command.startsWith("SEND,")) {

    int first = command.indexOf(',');
    int second = command.indexOf(',', first + 1);
    int third = command.indexOf(',', second + 1);

    if (first < 0 || second < 0 || third < 0) return;

    int module = command.substring(first + 1, second).toInt();

    int destination =
      command.substring(second + 1, third).toInt();

    String payload = command.substring(third + 1);

    if (module < 1 || module > 2) return;

    if (destination < 0 || destination > 65535) {
      dashboardMessage("ERROR|Invalid destination");
      return;
    }

    if (payload.length() == 0 || payload.length() > 240) {
      dashboardMessage("ERROR|Message must be 1-240 bytes");
      return;
    }

    String sendCommand =
      "AT+SEND=" +
      String(destination) + "," +
      String(payload.length()) + "," +
      payload;

    sendRadioCommand(module, sendCommand);

    return;
  }

  // Direct AT command
  // AT,module,command
  if (command.startsWith("AT,")) {

    int first = command.indexOf(',');
    int second = command.indexOf(',', first + 1);

    if (second < 0) return;

    int module = command.substring(first + 1, second).toInt();
    String atCommand = command.substring(second + 1);

    if (module >= 1 && module <= 2) {
      sendRadioCommand(module, atCommand);
    }

    return;
  }

  dashboardMessage("ERROR|Unknown command: " + command);
}

// =====================================================
// READ PC USB SERIAL
// =====================================================

void readUSB() {

  while (Serial.available()) {

    char c = (char)Serial.read();

    if (c == '\r') continue;

    if (c == '\n') {

      processCommand(usbBuffer);
      usbBuffer = "";

    } else if (usbBuffer.length() < 600) {

      usbBuffer += c;
    }
  }
}

// =====================================================
// SETUP
// =====================================================

void setup() {

  Serial.begin(USB_BAUD);

  LoRa1.begin(
    LORA_BAUD,
    SERIAL_8N1,
    LORA1_RX,
    LORA1_TX
  );

  LoRa2.begin(
    LORA_BAUD,
    SERIAL_8N1,
    LORA2_RX,
    LORA2_TX
  );

  LoRa1.setTimeout(50);
  LoRa2.setTimeout(50);

  delay(1000);

  dashboardMessage("STATUS|ESP32 dual LoRa gateway ready");
  dashboardMessage("STATUS|Module 1 UART2 GPIO16/17");
  dashboardMessage("STATUS|Module 2 UART1 GPIO25/26");
  dashboardMessage("STATUS|USB serial 115200");
}

// =====================================================
// MAIN LOOP
// =====================================================

void loop() {

  readUSB();

  readRadio(LoRa1, radioBuffer1, 1);
  readRadio(LoRa2, radioBuffer2, 2);

  if (millis() - lastHeartbeat >= 10000) {
    lastHeartbeat = millis();
    dashboardMessage("HEARTBEAT|ESP32");
  }
}

