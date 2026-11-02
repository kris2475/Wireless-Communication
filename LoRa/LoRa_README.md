# Bidirectional LoRa Communication Using ESP32 and MSP430

## Overview

This project demonstrates bidirectional point-to-point wireless communication using two REYAX RYLR896 LoRa modules.

The system consists of two independently addressed nodes:

- **Node 101:** ESP32 DevKit V1
- **Node 102:** MSP-EXP430F5529LP LaunchPad

Both modules operate on Network ID 6 and communicate using AT commands over UART. Messages can be transmitted manually through either node's USB Serial Monitor.

The ESP32 also supports push-button transmission using GPIO0.

## System Architecture

| Parameter | Node 101 | Node 102 |
|---|---|---|
| Microcontroller | ESP32 DevKit V1 | MSP-EXP430F5529LP |
| LoRa module | REYAX RYLR896 | REYAX RYLR896 |
| LoRa address | 101 | 102 |
| Network ID | 6 | 6 |
| UART baud rate | 115200 | 115200 |
| Serial monitor baud rate | 115200 | 9600 |
| Communication | Bidirectional | Bidirectional |

## Hardware Connections

### Node 101 – ESP32 DevKit V1

The RYLR896 is connected to UART2.

| ESP32 | RYLR896 |
|---|---|
| GPIO17 (TX2) | RXD |
| GPIO16 (RX2) | TXD |
| GND | GND |
| Appropriate supply | VCC |

A push-button is connected between GPIO0 and GND. The ESP32 internal pull-up resistor is enabled in software.

### Node 102 – MSP-EXP430F5529LP

The RYLR896 is connected to the MSP430 USCI_A0 hardware UART.

| MSP430F5529LP | RYLR896 |
|---|---|
| P3.3 (UCA0TXD) | RXD |
| P3.4 (UCA0RXD) | TXD |
| GND | GND |
| Appropriate supply | VCC |

The UART connections are crossed: TX connects to RXD, and RX connects to TXD.

**Important:** Ensure that the RYLR896 supply voltage and UART logic levels are compatible with the respective development boards.

## Node 101 – ESP32 Configuration

| Parameter | Setting |
|---|---|
| Address | 101 |
| Network ID | 6 |
| UART | UART2 |
| RX pin | GPIO16 |
| TX pin | GPIO17 |
| UART baud rate | 115200 |
| Serial monitor baud rate | 115200 |

The ESP32 configures the RYLR896 at startup using:

AT+NETWORKID=6
AT+ADDRESS=101

### Sending from Node 101 to Node 102

Enter the following command into the ESP32 Serial Monitor:

AT+SEND=102,26,Hello from ESP32 Node 101!

Alternatively, press the button connected to GPIO0 to transmit the predefined message.

### Receiving at Node 101

Messages received from Node 102 are forwarded to the ESP32 USB Serial Monitor.

## Node 102 – MSP430 Configuration

| Parameter | Setting |
|---|---|
| Address | 102 |
| Network ID | 6 |
| UART | USCI_A0 |
| TX pin | P3.3 |
| RX pin | P3.4 |
| UART baud rate | 115200 |
| Serial monitor baud rate | 9600 |

The MSP430 configures the RYLR896 at startup using:

AT
AT+ADDRESS=102
AT+NETWORKID=6
AT+ADDRESS?
AT+NETWORKID?

### Sending from Node 102 to Node 101

Enter the following command into the MSP430 Serial Monitor:

AT+SEND=101,26,Hello from MSP430 Node 102!

### Receiving at Node 102

Messages received from Node 101 are forwarded to the MSP430 USB Serial Monitor.

## AT Command Reference

The RYLR896 uses the following command format for transmission:

AT+SEND=<destination address>,<message length>,<message>

### Examples:

- **Node 101 to Node 102:**
  AT+SEND=102,26,Hello from ESP32 Node 101!
- **Node 102 to Node 101:**
  AT+SEND=101,26,Hello from MSP430 Node 102!

*Note: The message length must match the number of characters in the transmitted message.*

## Message Reception Format

The RYLR896 reports received messages using the following format:

+RCV=<sender address>,<message length>,<message>,<RSSI>,<SNR>

For example:

+RCV=101,26,Hello from ESP32 Node 101!,-45,10

RSSI and SNR values are supplied by the receiving module and depend on radio link conditions.

## Serial Interface Architecture

### Node 101 – ESP32

| Interface | Purpose |
|---|---|
| Serial | USB connection to PC |
| loraSerial | UART2 connection to RYLR896 |

### Node 102 – MSP430

| Interface | Purpose |
|---|---|
| Serial | USB diagnostic interface |
| Serial1 | USCI_A0 connection to RYLR896 |

Both nodes provide a serial bridge between the PC and the LoRa module, allowing AT commands to be entered manually and received messages to be displayed.

## Project Summary

The project establishes a bidirectional LoRa communication link between two different microcontroller platforms using identical RYLR896 radio modules.

- **ESP32 DevKit V1** operates as Node 101.
- **MSP-EXP430F5529LP** operates as Node 102.
- Both nodes use Network ID 6.
- Both modules communicate over UART at 115200 baud.
- AT commands provide direct control of the radio modules.
- USB serial interfaces provide manual command entry and message monitoring.
- Node 101 additionally supports push-button message transmission.

The implementation demonstrates cross-platform serial communication and point-to-point LoRa messaging using low-cost embedded hardware.
