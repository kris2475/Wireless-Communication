#include <HardwareSerial.h>

HardwareSerial loraSerial(2); 
const int buttonPin = 0;       
int lastButtonState = HIGH;

void setup() {
  Serial.begin(115200);                 
  loraSerial.begin(115200, SERIAL_8N1, 16, 17);
  delay(1500);

  pinMode(buttonPin, INPUT_PULLUP);

  loraSerial.println("AT+NETWORKID=6");
  delay(200);
  loraSerial.println("AT+ADDRESS=101");
  delay(200);
  
  Serial.println("ESP32 Node 101 Ready & Configured!");
}

void loop() {
  // Forward manual PC typing to the LoRa module
  if (Serial.available()) {
    loraSerial.write(Serial.read());
  }

  // Forward incoming LoRa module responses or packets to PC monitor
  if (loraSerial.available()) {
    Serial.write(loraSerial.read());
  }

  // Handle button press
  int buttonState = digitalRead(buttonPin);
  if (buttonState == LOW && lastButtonState == HIGH) {
    String msg = "Hello from ESP32 Node 101!";
    String cmd = "AT+SEND=102," + String(msg.length()) + "," + msg;
    
    Serial.println("Sending: " + msg);
    loraSerial.println(cmd);
    delay(500); 
  }
  lastButtonState = buttonState;
}