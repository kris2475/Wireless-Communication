# ESP32 Dual RYLR896 LoRa Controller & GUI Dashboard

A complete, dual-module LoRa communication system powered by an ESP32 microcontroller running custom Arduino firmware and managed via a full-featured Python/Tkinter desktop dashboard. This project allows for simultaneous configuration, bidirectional messaging, and live monitoring of two independent RYLR896 LoRa modules over hardware UART.

---

## System Overview

* Microcontroller (ESP32): Manages two separate hardware serial interfaces (HardwareSerial LoRa1 on UART2 and HardwareSerial LoRa2 on UART1) to interface simultaneously with dual RYLR896 transceiver modules. It parses live AT command setups, handles packet forwarding, and feeds real-time RSSI and payload logs back to the host computer.
* Desktop Control Software (Python/Tkinter): Provides an intuitive GUI dashboard featuring a live COM port selector, real-time status indicators, a startup/system debug console, live AT configuration parameter sync (Addresses, Network ID, Frequency Band, RF Power), and dedicated split-pane messaging consoles for Module 1 and Module 2 with custom color-coded TX/RX logs.

---

## Hardware Setup

<p align="center">
  <img src="/ESP32_Dual_LoRa_Stream/IMG20261103101530.jpg" width="600" alt="ESP32 Dual RYLR896 Hardware Setup">
</p>
<p align="center"><em>Figure 1: Complete hardware wiring of the ESP32 breadboard setup connected to dual RYLR896 LoRa modules.</em></p>

---

## Software in Action

<p align="center">
  <img src="/ESP32_Dual_LoRa_Stream/Recording2026-11-03125901-ezgif.com-speed.jpg" width="800" alt="ESP32 Dual RYLR896 Dashboard Animation">
</p>
<p align="center"><em>Figure 2: Live demonstration of the Python GUI dashboard controlling communication parameters and exchanging messages between modules.</em></p>

---

## Features

* Dual-Module Management: Independently configure and communicate with two RYLR896 LoRa transceivers from a single microcontroller and control interface.
* Live AT Parameter Synchronization: Instantly update radio parameters (Addresses, Network ID, Frequency, and RF Power output up to 20 dBm) directly from the GUI.
* Real-time RSSI Tracking & Parsing: Automatically extracts sender addresses, payloads, and signal strength (RSSI) from incoming radio broadcast events.
* Interactive GUI Dashboard: Built with Python's tkinter and pyserial, featuring automatic port refreshing, connection state tracking, auto-scrolling log windows, and color-coded transaction logs (TX in blue, RX in green).
