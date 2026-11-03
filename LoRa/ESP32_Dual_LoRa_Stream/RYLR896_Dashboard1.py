#!/usr/bin/env python3
import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports

class FullLoRaDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ESP32 Dual RYLR896 Full Control Dashboard")
        self.geometry("1550x900")
        self.minsize(1200, 750)

        self.ser = None
        self.is_connected = False
        self.auto_scroll = tk.BooleanVar(value=True)

        self._build_ui()
        self.refresh_ports()
        self.poll_serial()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=2)

        # --- TOP CONTROL BAR ---
        top_frame = ttk.Frame(self, padding="8")
        top_frame.grid(row=0, column=0, sticky="ew")

        ttk.Label(top_frame, text="COM Port:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=5)
        self.port_combo = ttk.Combobox(top_frame, width=15, state="readonly")
        self.port_combo.pack(side="left", padx=5)

        ttk.Button(top_frame, text="Refresh", command=self.refresh_ports).pack(side="left", padx=3)
        self.btn_connect = ttk.Button(top_frame, text="Connect", command=self.toggle_connection)
        self.btn_connect.pack(side="left", padx=3)

        self.lbl_status = ttk.Label(top_frame, text="Disconnected", font=("Segoe UI", 10, "bold"), foreground="#e74c3c")
        self.lbl_status.pack(side="left", padx=15)

        ttk.Button(top_frame, text="Clear All", command=self.clear_logs).pack(side="right", padx=3)
        ttk.Checkbutton(top_frame, text="Auto-scroll", variable=self.auto_scroll).pack(side="right", padx=10)

        # --- CONFIG PANEL ---
        cfg_frame = ttk.LabelFrame(self, text=" Radio Configuration Parameters (Live AT Command Sync) ", padding="8")
        cfg_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        ttk.Label(cfg_frame, text="M1 Addr:").pack(side="left", padx=3)
        self.ent_m1_addr = ttk.Entry(cfg_frame, width=6)
        self.ent_m1_addr.insert(0, "101")
        self.ent_m1_addr.pack(side="left", padx=3)

        ttk.Label(cfg_frame, text="M2 Addr:").pack(side="left", padx=3)
        self.ent_m2_addr = ttk.Entry(cfg_frame, width=6)
        self.ent_m2_addr.insert(0, "102")
        self.ent_m2_addr.pack(side="left", padx=3)

        ttk.Label(cfg_frame, text="Network ID:").pack(side="left", padx=3)
        self.ent_net = ttk.Entry(cfg_frame, width=6)
        self.ent_net.insert(0, "6")
        self.ent_net.pack(side="left", padx=3)

        ttk.Label(cfg_frame, text="Band (Hz):").pack(side="left", padx=3)
        self.ent_band = ttk.Entry(cfg_frame, width=12)
        self.ent_band.insert(0, "868000000")
        self.ent_band.pack(side="left", padx=3)

        ttk.Label(cfg_frame, text="RF Power (dBm):").pack(side="left", padx=3)
        self.power_combo = ttk.Combobox(cfg_frame, width=6, state="readonly")
        self.power_combo["values"] = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"]
        self.power_combo.set("2")
        self.power_combo.pack(side="left", padx=3)

        ttk.Button(cfg_frame, text="Apply Config", command=self.apply_config).pack(side="left", padx=15)

        # --- STARTUP LOG WINDOW ---
        w1_outer = ttk.LabelFrame(self, text=" Startup & System Debug Log ", padding="5")
        w1_outer.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        w1_outer.columnconfigure(0, weight=1)
        w1_outer.rowconfigure(0, weight=1)

        self.txt_startup = tk.Text(w1_outer, bg="#0d1117", fg="#c9d1d9", font=("Consolas", 9), wrap="word", relief="flat", height=6)
        self.txt_startup.grid(row=0, column=0, sticky="nsew")
        st_scroll = ttk.Scrollbar(w1_outer, orient="vertical", command=self.txt_startup.yview)
        st_scroll.grid(row=0, column=1, sticky="ns")
        self.txt_startup.configure(yscrollcommand=st_scroll.set)

        self.txt_startup.tag_config("READY", foreground="#2ecc71", font=("Consolas", 9, "bold"))
        self.txt_startup.tag_config("NORMAL", foreground="#c9d1d9")

        # --- BOTTOM DIALOGUE CONTAINER ---
        bottom_container = ttk.Frame(self)
        bottom_container.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        bottom_container.columnconfigure(0, weight=1)
        bottom_container.columnconfigure(1, weight=1)
        bottom_container.rowconfigure(0, weight=1)

        # --- MODULE 1 DIALOGUE ---
        self.m1_outer = ttk.LabelFrame(bottom_container, text=" Module 1 (Address: 101) ", padding="8")
        self.m1_outer.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.m1_outer.columnconfigure(0, weight=1)
        self.m1_outer.rowconfigure(0, weight=1)

        m1_inner_frame = ttk.Frame(self.m1_outer)
        m1_inner_frame.grid(row=0, column=0, sticky="nsew")
        m1_inner_frame.columnconfigure(0, weight=1)
        m1_inner_frame.rowconfigure(0, weight=1)

        self.txt_m1 = tk.Text(m1_inner_frame, bg="#0d1117", font=("Consolas", 10), wrap="word", relief="flat")
        self.txt_m1.grid(row=0, column=0, sticky="nsew", columnspan=2)
        m1_scroll = ttk.Scrollbar(m1_inner_frame, orient="vertical", command=self.txt_m1.yview)
        m1_scroll.grid(row=0, column=2, sticky="ns")
        self.txt_m1.configure(yscrollcommand=m1_scroll.set)

        ttk.Label(m1_inner_frame, text="Send to Dest:").grid(row=1, column=0, sticky="w", pady=5)
        self.ent_m1_dest = ttk.Entry(m1_inner_frame, width=8)
        self.ent_m1_dest.insert(0, "102")
        self.ent_m1_dest.grid(row=1, column=0, sticky="w", padx=80, pady=5)

        self.ent_m1_msg = ttk.Entry(m1_inner_frame, width=30)
        self.ent_m1_msg.insert(0, "Hello from M1!")
        self.ent_m1_msg.grid(row=2, column=0, sticky="ew", pady=5)
        self.ent_m1_msg.bind("<Return>", lambda e: self.send_message(1))
        ttk.Button(m1_inner_frame, text="Send M1", command=lambda: self.send_message(1)).grid(row=2, column=1, padx=5, pady=5)

        # --- MODULE 2 DIALOGUE ---
        self.m2_outer = ttk.LabelFrame(bottom_container, text=" Module 2 (Address: 102) ", padding="8")
        self.m2_outer.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.m2_outer.columnconfigure(0, weight=1)
        self.m2_outer.rowconfigure(0, weight=1)

        m2_inner_frame = ttk.Frame(self.m2_outer)
        m2_inner_frame.grid(row=0, column=0, sticky="nsew")
        m2_inner_frame.columnconfigure(0, weight=1)
        m2_inner_frame.rowconfigure(0, weight=1)

        self.txt_m2 = tk.Text(m2_inner_frame, bg="#0d1117", font=("Consolas", 10), wrap="word", relief="flat")
        self.txt_m2.grid(row=0, column=0, sticky="nsew", columnspan=2)
        m2_scroll = ttk.Scrollbar(m2_inner_frame, orient="vertical", command=self.txt_m2.yview)
        m2_scroll.grid(row=0, column=2, sticky="ns")
        self.txt_m2.configure(yscrollcommand=m2_scroll.set)

        ttk.Label(m2_inner_frame, text="Send to Dest:").grid(row=1, column=0, sticky="w", pady=5)
        self.ent_m2_dest = ttk.Entry(m2_inner_frame, width=8)
        self.ent_m2_dest.insert(0, "101")
        self.ent_m2_dest.grid(row=1, column=0, sticky="w", padx=80, pady=5)

        self.ent_m2_msg = ttk.Entry(m2_inner_frame, width=30)
        self.ent_m2_msg.insert(0, "Hello from M2!")
        self.ent_m2_msg.grid(row=2, column=0, sticky="ew", pady=5)
        self.ent_m2_msg.bind("<Return>", lambda e: self.send_message(2))
        ttk.Button(m2_inner_frame, text="Send M2", command=lambda: self.send_message(2)).grid(row=2, column=1, padx=5, pady=5)

        for w in [self.txt_m1, self.txt_m2]:
            w.tag_config("TX", foreground="#58a6ff")
            w.tag_config("RX", foreground="#2ecc71")

    def refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo["values"] = ports
        if ports and not self.port_combo.get():
            self.port_combo.set(ports[0])

    def toggle_connection(self):
        if self.is_connected:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        port = self.port_combo.get()
        if not port:
            messagebox.showerror("Error", "Please select a valid COM port.")
            return

        try:
            self.ser = serial.Serial(port, 115200, timeout=0.1)
            self.is_connected = True
            self.btn_connect.config(text="Disconnect")
            self.lbl_status.config(text=f"Connected ({port}) - Initializing...", foreground="#f39c12")
            self._log_startup("SYSTEM", f"Connected to {port} at 115200 baud. Waiting for initialization...")
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def disconnect_serial(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.is_connected = False
        self.btn_connect.config(text="Connect")
        self.lbl_status.config(text="Disconnected", foreground="#e74c3c")

    def apply_config(self):
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to the ESP32 first.")
            return

        m1_a = self.ent_m1_addr.get()
        m2_a = self.ent_m2_addr.get()
        net = self.ent_net.get()
        band = self.ent_band.get()
        pwr = self.power_combo.get()

        if not m1_a or not m2_a or not net or not band or not pwr:
            messagebox.showerror("Error", "All configuration fields must be filled.")
            return

        cfg_str = f"CONFIG:{m1_a},{m2_a},{net},{band},{pwr}\n"
        self.ser.write(cfg_str.encode("utf-8"))

        self.m1_outer.config(text=f" Module 1 (Address: {m1_a}) ")
        self.m2_outer.config(text=f" Module 2 (Address: {m2_a}) ")
        self.ent_m1_dest.delete(0, tk.END)
        self.ent_m1_dest.insert(0, m2_a)
        self.ent_m2_dest.delete(0, tk.END)
        self.ent_m2_dest.insert(0, m1_a)

        self._log_startup("UI", f"Re-applying Config -> M1 Addr:{m1_a}, M2 Addr:{m2_a}, Net:{net}, Band:{band}, Power:{pwr}dBm")

    def send_message(self, module_num):
        if not self.is_connected:
            messagebox.showwarning("Warning", "Not connected to ESP32.")
            return

        dest = self.ent_m1_dest.get() if module_num == 1 else self.ent_m2_dest.get()
        msg = self.ent_m1_msg.get() if module_num == 1 else self.ent_m2_msg.get()
        target_widget = self.txt_m1 if module_num == 1 else self.txt_m2

        if not dest or not msg:
            return

        cmd_str = f"SEND{module_num}:{dest},{msg}\n"
        self.ser.write(cmd_str.encode("utf-8"))

        now = datetime.datetime.now().strftime("%H:%M:%S")
        target_widget.insert(tk.END, f"[{now}] [TX OUT] Sent to Node {dest}: \"{msg}\"\n", "TX")
        target_widget.see(tk.END)

        if module_num == 1:
            self.ent_m1_msg.delete(0, tk.END)
        else:
            self.ent_m2_msg.delete(0, tk.END)

    def _log_startup(self, tag, text, is_ready=False):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        tag_name = "READY" if is_ready else "NORMAL"
        self.txt_startup.insert(tk.END, f"[{now}] [{tag}] {text}\n", tag_name)
        if self.auto_scroll.get():
            self.txt_startup.see(tk.END)

    def clear_logs(self):
        self.txt_startup.delete("1.0", tk.END)
        self.txt_m1.delete("1.0", tk.END)
        self.txt_m2.delete("1.0", tk.END)

    def poll_serial(self):
        if self.is_connected and self.ser and self.ser.is_open:
            try:
                while self.ser.in_waiting:
                    line = self.ser.readline().decode("utf-8", errors="replace").strip()
                    if not line:
                        continue

                    # Catch existing Arduino configuration completion string and trigger green status
                    if "[CONFIG_APPLIED]" in line:
                        self.lbl_status.config(text="Connected & Ready", foreground="#2ecc71")
                        self._log_startup("SUCCESS", "INITIALIZATION COMPLETE. ALL SYSTEMS GO!", is_ready=True)
                    else:
                        self._log_startup("ESP32", line)

                    if "[RX_EVENT]" in line:
                        now = datetime.datetime.now().strftime("%H:%M:%S")
                        if "Target:MODULE 1" in line:
                            self.txt_m1.insert(tk.END, f"[{now}] [RX IN ] {line}\n", "RX")
                            self.txt_m1.see(tk.END)
                        elif "Target:MODULE 2" in line:
                            self.txt_m2.insert(tk.END, f"[{now}] [RX IN ] {line}\n", "RX")
                            self.txt_m2.see(tk.END)
            except Exception as e:
                self.disconnect_serial()

        self.after(50, self.poll_serial)

if __name__ == "__main__":
    app = FullLoRaDashboard()
    app.mainloop()