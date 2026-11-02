
/*
 * MSP-EXP430F5529LP - RYLR896 Node 102
 *
 * USB diagnostic: Serial
 * LoRa UART:      Serial1 (USCI_A0)
 *
 * UART pins:
 *   P3.3 TX -> RYLR896 RXD
 *   P3.4 RX <- RYLR896 TXD
 *
 * LoRa configuration:
 *   Address:   102
 *   NetworkID: 6
 *   Baud:      115200
 */

#define LORA_BAUD 115200

// Send an AT command and display its response.
void sendAT(const char *command)
{
  Serial.println();
  Serial.print("Sending: ");
  Serial.println(command);

  // Clear previous received data.
  while (Serial1.available())
  {
    Serial1.read();
  }

  // Send command.
  Serial1.print(command);
  Serial1.print("\r\n");

  // Read response.
  unsigned long start = millis();
  bool received = false;

  while (millis() - start < 1500)
  {
    while (Serial1.available())
    {
      char c = Serial1.read();

      if (!received)
      {
        Serial.print("RYLR896: ");
        received = true;
      }

      Serial.write(c);
      start = millis();
    }
  }

  if (!received)
  {
    Serial.println("NO RESPONSE");
  }

  Serial.println();
}

void setup()
{
  // USB diagnostic connection.
  Serial.begin(9600);

  delay(2000);

  Serial.println();
  Serial.println("==============================");
  Serial.println("MSP430F5529 - LORA NODE 102");
  Serial.println("==============================");

  // External hardware UART on P3.3/P3.4.
  Serial1.begin(LORA_BAUD);

  delay(500);

  // Test communication.
  sendAT("AT");

  // Configure RYLR896.
  sendAT("AT+ADDRESS=102");
  sendAT("AT+NETWORKID=6");

  // Verify configuration.
  sendAT("AT+ADDRESS?");
  sendAT("AT+NETWORKID?");

  Serial.println();
  Serial.println("==============================");
  Serial.println("NODE 102 READY");
  Serial.println("==============================");
}

void loop()
{
  // RYLR896 -> USB Serial Monitor.
  while (Serial1.available())
  {
    Serial.write(Serial1.read());
  }

  // USB Serial Monitor -> RYLR896.
  while (Serial.available())
  {
    Serial1.write(Serial.read());
  }
}
