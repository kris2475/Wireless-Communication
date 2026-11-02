# XBee S2C Wireless Communication with MSP-ESP430F5529LP

This repository details the configuration, hardware setup, and testing for establishing a wireless serial communication link between two **XBee S2C** modules using **Digi XCTU**, an **MSP-ESP430F5529LP** microcontroller board, and a Hobbytronics XBee-USB adapter.

---

## Hardware Architecture

1. **Coordinator Node**:
   * **XBee S2C Module** configured as a **Coordinator** (`CE = 1`)[cite: 1].
   * Mounted on a **Hobbytronics XBee-USB board** and connected to a host computer via USB.
   * Controlled and monitored through the **XCTU console**.

   <p align="center">
     <img src="Coordinator.jpg" alt="Coordinator Setup" width="400"/>
   </p>

2. **End Device Node**:
   * **XBee S2C Module** configured as an **End Device** (`CE = 0`)[cite: 1].
   * Connected via jumper wires to an **MSP-ESP430F5529LP** LaunchPad board.

   <p align="center">
     <img src="End_Device.jpg" alt="End Device Setup" width="400"/>
   </p>

---

## XBee S2C Configuration (via XCTU)

Both modules were configured using Digi XCTU under the **802.15.4** protocol firmware[cite: 1]:

### Common Parameters
* **PAN ID (`ID`)**: `1234`[cite: 1]
* **Channel (`CH`)**: `C`[cite: 1]
* **Baud Rate (`BD`)**: `9600`[cite: 1] (or `115200` depending on interface settings)

### Coordinator Settings
* **Coordinator Enable (`CE`)**: `Coordinator [1]`[cite: 1]
* **MAC Mode (`MM`)**: `802.15.4 + MaxStream header no ACKS [3]`[cite: 1]

### End Device Settings
* **Coordinator Enable (`CE`)**: `End Device [0]`[cite: 1]
* **MAC Mode (`MM`)**: `802.15.4 + MaxStream header w/ACKS [0]`[cite: 1]

---

## MSP430 Firmware

The MSP-ESP430F5529LP acts as a serial bridge passing data back and forth between its hardware serial interfaces (`Serial` and `Serial1`):

```cpp
void setup() {
  // initialize both serial ports:
  Serial.begin(9600);
  Serial1.begin(9600);
}

void loop() {
  // read from port 1, send to port 0:
  if (Serial1.available()) {
    int inByte1 = Serial1.read();
    Serial.write(inByte1);
  }

  // read from port 0, send to port 1:
  if (Serial.available()) {
    int inByte0 = Serial.read();
    Serial1.write(inByte0);
  }
}
