# ESP32 Dual RYLR896 LoRa Communication System

## Overview

This project uses an ESP32 DevKit V1 to interface with two REYAX RYLR896 LoRa modules through independent hardware UART interfaces.

The ESP32 acts as a gateway between a PC-based Python dashboard and the two LoRa radios. The dashboard allows the user to configure each radio, transmit messages, and monitor incoming and outgoing serial communication.

The two radio modules are configured with different addresses but share the same LoRa network ID.

### System configuration

| Parameter | Module 1 | Module 2 |
|---|---:|---:|
| ESP32 UART | UART2 | UART1 |
| ESP32 RX pin | GPIO16 | GPIO25 |
| ESP32 TX pin | GPIO17 | GPIO26 |
| LoRa address | 101 | 102 |
| Network ID | 6 | 6 |
| UART baud rate | 115200 | 115200 |

## Hardware

- ESP32 DevKit V1
- 2 × REYAX RYLR896 LoRa modules
- USB cable for ESP32 programming and PC communication
- Suitable regulated power supply for the radio modules
- Common ground between the ESP32 and both radio modules

Check the frequency variant and regional radio regulations before transmitting. The hardware and configuration must be suitable for the intended regional frequency band and permitted operating parameters.

## Wiring

Each RYLR896 module is connected to a separate ESP32 hardware UART.

### Module 1 — LoRa address 101

| RYLR896 pin | ESP32 pin |
|---|---|
| TX | GPIO16 (UART2 RX) |
| RX | GPIO17 (UART2 TX) |
| GND | GND |
| VCC | Suitable regulated supply |

### Module 2 — LoRa address 102

| RYLR896 pin | ESP32 pin |
|---|---|
| TX | GPIO25 (UART1 RX) |
| RX | GPIO26 (UART1 TX) |
| GND | GND |
| VCC | Suitable regulated supply |

**Important:** UART1 was initially tested on GPIO32 and GPIO33. That pin assignment did not work reliably in this setup. Moving UART1 to GPIO25 and GPIO26 resolved the problem.

The UART connections are crossed:

- Radio TX connects to ESP32 RX.
- Radio RX connects to ESP32 TX.
- All devices share a common ground.

Check the RYLR896 module's supply-voltage requirements before connecting its power input. Do not assume that the ESP32 3.3 V output can supply the radio's peak current requirements.

## Radio configuration

Both modules use a UART baud rate of 115200 and LoRa network ID 6.

The configured radio addresses are:

- Module 1: `101`
- Module 2: `102`

The following AT commands were used to configure and verify the modules.

| Command | Purpose | Expected response |
|---|---|---|
| `AT` | Check radio response | `+OK` |
| `AT+ADDRESS=101` | Set Module 1 address | `+OK` |
| `AT+ADDRESS=102` | Set Module 2 address | `+OK` |
| `AT+ADDRESS?` | Read radio address | `+ADDRESS=...` |
| `AT+NETWORKID=6` | Set network ID | `+OK` |
| `AT+NETWORKID?` | Read network ID | `+NETWORKID=6` |
| `AT+IPR?` | Read UART baud rate | `+IPR=115200` |

The actual read-back response for the network setting is `+NETWORKID=6`.

### Verified hardware configuration

The following checks were completed successfully:

- Module 1, connected through UART2 on GPIO16/GPIO17, returned `+OK` to `AT`.
- Module 1 address was verified as 101.
- Module 1 network ID was verified as 6.
- Module 1 UART baud rate was verified as 115200.
- Module 2, connected through UART1 on GPIO25/GPIO26, returned `+OK` to `AT`.
- Module 2 address was verified as 102.
- Module 2 network ID was verified as 6.
- Module 2 UART baud rate was verified as 115200.
- Both modules accepted outgoing `AT+SEND` commands and returned `+OK`.

A response of `+OK` to an `AT+SEND` command confirms that the transmitting radio accepted the command. It does not, by itself, prove that the other radio received the message. Successful over-the-air reception is confirmed by the receiving radio reporting a `+RCV` message.

## Software architecture

The system consists of two software components.

### 1. ESP32 gateway firmware

File: `ESP32_Dual_RYLR896_Dashboard.ino`

The ESP32 firmware:

- Opens two independent hardware UART interfaces.
- Communicates with both RYLR896 modules.
- Receives commands from the PC over USB serial.
- Routes commands to the selected LoRa module.
- Forwards radio responses and received messages to the PC.
- Provides a simple serial command interface for the Python dashboard.

The UART configuration is:

```cpp
HardwareSerial LoRa1(2);
HardwareSerial LoRa2(1);

#define LORA1_RX 16
#define LORA1_TX 17

#define LORA2_RX 25
#define LORA2_TX 26

#define LORA_BAUD 115200
#define USB_BAUD 115200
```

### 2. Python dashboard

File: `RYLR896_Dashboard.py`

The Python application provides a graphical interface for controlling and monitoring the two LoRa modules.

Features include:

- Serial COM port selection and refresh.
- Connect and disconnect controls.
- Separate configuration panels for Module 1 and Module 2.
- Editable LoRa addresses and network IDs.
- Apply configuration and read-back functions.
- Selection of the transmitting module.
- Destination address selection.
- Message entry and transmission.
- Automatic UTF-8 message-length display.
- Live timestamped communication log.
- Separate display of transmit, receive, status and error messages.
- Clear log function.
- Save communication log to a text file.
- Automatic scrolling of the communication log.

## Python requirements

Install Python 3 and the PySerial package:

```bash
pip install pyserial
```

The dashboard uses Tkinter for its graphical interface. Tkinter is included with many standard Python installations. On Linux, it may need to be installed separately through the operating system's package manager.

Run the dashboard with:

```bash
python RYLR896_Dashboard.py
```

## Operating procedure

1. Connect both RYLR896 modules to the ESP32 using the wiring shown above.
2. Connect the ESP32 to the PC using USB.
3. Upload `ESP32_Dual_RYLR896_Dashboard.ino` to the ESP32.
4. Start `RYLR896_Dashboard.py`.
5. Select the ESP32 COM port.
6. Connect to the ESP32.
7. Allow the dashboard to query both radio modules.
8. Check that the reported addresses, network IDs and UART settings are correct.
9. Select the transmitting module.
10. Enter the destination radio address.
11. Enter a message and transmit it.
12. Check the receiving module's log for the corresponding `+RCV` response.

The default configuration is:

| Setting | Value |
|---|---|
| Module 1 address | 101 |
| Module 2 address | 102 |
| Network ID | 6 |
| Radio UART baud rate | 115200 |
| ESP32 USB serial baud rate | 115200 |

## ESP32 USB serial command interface

The Python dashboard communicates with the ESP32 using newline-terminated commands over USB serial at 115200 baud.

The gateway supports the following commands.

| Command | Description |
|---|---|
| `PING` | Check that the ESP32 gateway is responding |
| `QUERY,module,ADDRESS` | Read the selected module's LoRa address |
| `QUERY,module,NETWORKID` | Read the selected module's network ID |
| `QUERY,module,IPR` | Read the selected module's UART baud rate |
| `CFG,module,ADDRESS,value` | Set the selected module's LoRa address |
| `CFG,module,NETWORKID,value` | Set the selected module's network ID |
| `SEND,module,destination,payload` | Send a message to a destination address |
| `AT,module,command` | Send an AT command directly to the selected module |

The `module` field identifies the radio:

- `1` selects Module 1.
- `2` selects Module 2.

For example, to send `Hello from Module 1` from Module 1 to Module 2:

```text
SEND,1,102,Hello from Module 1
```

To send a message in the opposite direction:

```text
SEND,2,101,Hello from Module 2
```

The gateway also supports payloads containing commas by treating the text after the third comma as the message payload.

### Gateway responses

The ESP32 forwards radio and system information to the Python dashboard using tagged serial messages.

| Prefix | Meaning |
|---|---|
| `LORA|module|...` | Response received from a LoRa module |
| `TXCMD|module|...` | AT command sent to a LoRa module |
| `STATUS|...` | Gateway or module status information |
| `HEARTBEAT|ESP32` | ESP32 gateway heartbeat |
| `ERROR|...` | Error reported by the gateway |
| `PONG|ESP32_DUAL_RYLR896` | Response to a `PING` command |

## Message transmission and reception

The RYLR896 modules use AT commands to transmit messages.

The general command format is:

```text
AT+SEND=destination,length,payload
```

For example:

```text
AT+SEND=102,19,Hello from Module 1
```

The length field represents the payload length in bytes. For ASCII messages, the character count and byte count are the same. For non-ASCII text, UTF-8 characters can occupy more than one byte, so the encoded byte length must be used.

A transmitting module normally returns:

```text
+OK
```

This confirms that the radio accepted the transmission command. The receiving module should report the received message in a response similar to:

```text
+RCV=101,19,Hello from Module 1,...
```

The exact fields following the payload depend on the RYLR896 response format.

**Do not treat the sender's `+OK` response as confirmation of successful reception.** Confirm delivery by checking for the corresponding `+RCV` message at the destination module.

## Troubleshooting

### Module does not respond to `AT`

Check:

- Radio power supply and ground.
- TX/RX crossover.
- UART baud rate.
- ESP32 UART pin assignments.
- Whether the selected UART is the one connected to the radio.

The expected response to `AT` is:

```text
+OK
```

### Module 2 does not communicate on GPIO32/GPIO33

The original UART1 assignment using GPIO32 and GPIO33 did not work reliably in this hardware configuration.

The working assignment is:

| Signal | ESP32 pin |
|---|---|
| UART1 RX | GPIO25 |
| UART1 TX | GPIO26 |

### The sender reports `+OK`, but no message appears at the receiver

A sender-side `+OK` only confirms that the radio accepted the command.

Check:

- Both modules are powered and responding.
- Both modules use the same network ID.
- The destination address is correct.
- Both modules use compatible frequency-band hardware and radio settings.
- The receiving module's UART connection and dashboard log are working.
- The radio modules are operating within the applicable regional regulations.

Look for a `+RCV` response from the receiving module.

### Incorrect address or network ID

Use the dashboard's query functions to read the current settings. Apply the required configuration and query the settings again to verify the result.

The expected settings are:

| Module | Address | Network ID |
|---|---:|---:|
| Module 1 | 101 | 6 |
| Module 2 | 102 | 6 |

### Garbled serial output

Check that the ESP32 USB serial monitor and Python dashboard use 115200 baud. Also check that the radio UART baud rate is configured as 115200 and that the correct UART pins are being used.

## Project status

The two-radio hardware configuration has been tested successfully.

Both RYLR896 modules responded to AT commands through their respective ESP32 hardware UART interfaces. Their addresses, network IDs and UART baud rates were read back successfully. Both modules also accepted outgoing send commands.

The working ESP32 pin assignments are:

- Module 1: UART2, GPIO16 RX and GPIO17 TX.
- Module 2: UART1, GPIO25 RX and GPIO26 TX.

The next verification step for any new deployment is to confirm actual over-the-air message reception by observing the corresponding `+RCV` response on the destination module.

## Potential future development

- Message acknowledgement and delivery confirmation.
- Automatic retry when a message is not received.
- Packet sequence numbers and duplicate detection.
- RSSI and SNR logging where supported by the radio response.
- Message history and CSV export.
- Multiple remote nodes.
- Periodic sensor-data transmission.
- Configurable transmission intervals.
- Improved connection and radio health monitoring.

## Licence

Add the chosen project licence here.
