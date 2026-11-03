
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import queue
import time
from datetime import datetime


# =========================================================
# CONFIGURATION
# =========================================================

BAUD_RATE = 115200
MAX_MESSAGE_BYTES = 240


# =========================================================
# DASHBOARD APPLICATION
# =========================================================

class LoRaDashboard:

    def __init__(self, root):

        self.root = root
        self.root.title("RYLR896 Dual LoRa Dashboard")
        self.root.geometry("1150x780")
        self.root.minsize(950, 650)

        self.serial_port = None
        self.reader_thread = None
        self.running = False

        self.event_queue = queue.Queue()

        self.module1_address = tk.StringVar(value="101")
        self.module2_address = tk.StringVar(value="102")

        self.module1_network = tk.StringVar(value="6")
        self.module2_network = tk.StringVar(value="6")

        self.selected_module = tk.StringVar(value="1")
        self.destination = tk.StringVar(value="102")

        self.message_text = tk.StringVar()

        self.port_selection = tk.StringVar()

        self.connection_status = tk.StringVar(
            value="Disconnected"
        )

        self.module1_status = tk.StringVar(
            value="Not connected"
        )

        self.module2_status = tk.StringVar(
            value="Not connected"
        )

        self.log_lines = []

        self.build_interface()
        self.refresh_ports()

        self.root.after(100, self.process_events)
        self.root.protocol("WM_DELETE_WINDOW", self.close_application)

    # =====================================================
    # INTERFACE
    # =====================================================

    def build_interface(self):

        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 19, "bold")
        )

        style.configure(
            "Heading.TLabel",
            font=("Segoe UI", 11, "bold")
        )

        style.configure(
            "Status.TLabel",
            font=("Segoe UI", 10, "bold")
        )

        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------

        header = ttk.Frame(main)
        header.pack(fill="x", pady=(0, 12))

        ttk.Label(
            header,
            text="RYLR896 LoRa Control Dashboard",
            style="Title.TLabel"
        ).pack(side="left")

        ttk.Label(
            header,
            textvariable=self.connection_status,
            style="Status.TLabel"
        ).pack(side="right")

        # -------------------------------------------------
        # SERIAL CONNECTION
        # -------------------------------------------------

        connection = ttk.LabelFrame(
            main,
            text="ESP32 USB Serial Connection",
            padding=10
        )

        connection.pack(fill="x", pady=5)

        ttk.Label(connection, text="COM Port:").pack(
            side="left", padx=5
        )

        self.port_combo = ttk.Combobox(
            connection,
            textvariable=self.port_selection,
            width=18,
            state="readonly"
        )

        self.port_combo.pack(side="left", padx=5)

        ttk.Button(
            connection,
            text="Refresh",
            command=self.refresh_ports
        ).pack(side="left", padx=5)

        self.connect_button = ttk.Button(
            connection,
            text="Connect",
            command=self.connect_serial
        )

        self.connect_button.pack(side="left", padx=5)

        self.disconnect_button = ttk.Button(
            connection,
            text="Disconnect",
            command=self.disconnect_serial,
            state="disabled"
        )

        self.disconnect_button.pack(side="left", padx=5)

        ttk.Label(
            connection,
            text="115200 baud"
        ).pack(side="right", padx=10)

        # -------------------------------------------------
        # MODULE CONFIGURATION
        # -------------------------------------------------

        modules = ttk.Frame(main)
        modules.pack(fill="x", pady=8)

        self.build_module_panel(
            modules,
            "MODULE 1",
            "UART2 | RX 16 | TX 17",
            self.module1_address,
            self.module1_network,
            self.module1_status,
            0
        )

        self.build_module_panel(
            modules,
            "MODULE 2",
            "UART1 | RX 25 | TX 26",
            self.module2_address,
            self.module2_network,
            self.module2_status,
            1
        )

        # -------------------------------------------------
        # MESSAGE COMPOSER
        # -------------------------------------------------

        composer = ttk.LabelFrame(
            main,
            text="Message Composer",
            padding=10
        )

        composer.pack(fill="x", pady=8)

        top = ttk.Frame(composer)
        top.pack(fill="x")

        ttk.Label(top, text="Sending module:").pack(
            side="left", padx=5
        )

        self.module_combo = ttk.Combobox(
            top,
            textvariable=self.selected_module,
            values=["1", "2"],
            state="readonly",
            width=8
        )

        self.module_combo.pack(side="left", padx=5)

        self.module_combo.bind(
            "<<ComboboxSelected>>",
            self.update_destination
        )

        ttk.Label(top, text="Destination address:").pack(
            side="left", padx=(20, 5)
        )

        self.destination_combo = ttk.Combobox(
            top,
            textvariable=self.destination,
            width=12
        )

        self.destination_combo.pack(side="left", padx=5)

        self.message_entry = ttk.Entry(
            composer,
            textvariable=self.message_text,
            font=("Segoe UI", 11)
        )

        self.message_entry.pack(
            fill="x", pady=10, ipady=5
        )

        self.message_entry.bind(
            "<Return>",
            lambda event: self.send_message()
        )

        bottom = ttk.Frame(composer)
        bottom.pack(fill="x")

        self.byte_count = ttk.Label(
            bottom,
            text="0 / 240 bytes"
        )

        self.byte_count.pack(side="left")

        self.message_text.trace_add(
            "write",
            self.update_byte_count
        )

        self.send_button = ttk.Button(
            bottom,
            text="SEND MESSAGE",
            command=self.send_message,
            state="disabled"
        )

        self.send_button.pack(side="right")

        # -------------------------------------------------
        # LIVE LOG
        # -------------------------------------------------

        log_frame = ttk.LabelFrame(
            main,
            text="Live Communications Monitor",
            padding=8
        )

        log_frame.pack(fill="both", expand=True, pady=8)

        toolbar = ttk.Frame(log_frame)
        toolbar.pack(fill="x", pady=(0, 5))

        ttk.Button(
            toolbar,
            text="Clear Log",
            command=self.clear_log
        ).pack(side="left", padx=3)

        ttk.Button(
            toolbar,
            text="Save Log",
            command=self.save_log
        ).pack(side="left", padx=3)

        self.auto_scroll = tk.BooleanVar(value=True)

        ttk.Checkbutton(
            toolbar,
            text="Auto-scroll",
            variable=self.auto_scroll
        ).pack(side="right", padx=5)

        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill="both", expand=True)

        self.log_display = tk.Text(
            text_frame,
            height=18,
            wrap="word",
            font=("Consolas", 9),
            state="disabled",
            background="#151b23",
            foreground="#e6edf3",
            insertbackground="white"
        )

        scrollbar = ttk.Scrollbar(
            text_frame,
            command=self.log_display.yview
        )

        self.log_display.configure(
            yscrollcommand=scrollbar.set
        )

        self.log_display.pack(
            side="left", fill="both", expand=True
        )

        scrollbar.pack(side="right", fill="y")

        self.log_display.tag_config(
            "TX", foreground="#58a6ff"
        )

        self.log_display.tag_config(
            "RX", foreground="#3fb950"
        )

        self.log_display.tag_config(
            "ERROR", foreground="#ff7b72"
        )

        self.log_display.tag_config(
            "SYSTEM", foreground="#d2a8ff"
        )

        self.log_display.tag_config(
            "STATUS", foreground="#e3b341"
        )

        # -------------------------------------------------
        # FOOTER
        # -------------------------------------------------

        footer = ttk.Frame(main)
        footer.pack(fill="x", pady=(5, 0))

        ttk.Label(
            footer,
            text="ESP32 USB Gateway | RYLR896 | 115200 baud"
        ).pack(side="left")

    # =====================================================
    # MODULE PANELS
    # =====================================================

    def build_module_panel(
        self,
        parent,
        title,
        hardware,
        address_var,
        network_var,
        status_var,
        column
    ):

        panel = ttk.LabelFrame(
            parent,
            text=title,
            padding=10
        )

        panel.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=5
        )

        parent.columnconfigure(column, weight=1)

        ttk.Label(
            panel,
            text=hardware
        ).grid(row=0, column=0, columnspan=3,
               sticky="w", pady=3)

        ttk.Label(panel, text="Address:").grid(
            row=1, column=0, sticky="w", pady=5
        )

        ttk.Entry(
            panel,
            textvariable=address_var,
            width=12
        ).grid(row=1, column=1, sticky="w")

        ttk.Label(panel, text="Network ID:").grid(
            row=2, column=0, sticky="w", pady=5
        )

        ttk.Entry(
            panel,
            textvariable=network_var,
            width=12
        ).grid(row=2, column=1, sticky="w")

        ttk.Button(
            panel,
            text="Apply Configuration",
            command=lambda: self.apply_configuration(
                1 if column == 0 else 2
            )
        ).grid(
            row=3, column=0, columnspan=2,
            sticky="ew", pady=7
        )

        ttk.Button(
            panel,
            text="Read Configuration",
            command=lambda: self.query_configuration(
                1 if column == 0 else 2
            )
        ).grid(
            row=4, column=0, columnspan=2,
            sticky="ew", pady=3
        )

        ttk.Label(
            panel,
            textvariable=status_var,
            style="Status.TLabel"
        ).grid(
            row=5, column=0, columnspan=3,
            sticky="w", pady=8
        )

    # =====================================================
    # PORT MANAGEMENT
    # =====================================================

    def refresh_ports(self):

        ports = serial.tools.list_ports.comports()

        port_names = [
            f"{port.device} - {port.description}"
            for port in ports
        ]

        self.port_combo["values"] = port_names

        if port_names:
            self.port_combo.current(0)
        else:
            self.port_selection.set("")

    def connect_serial(self):

        selection = self.port_selection.get()

        if not selection:
            messagebox.showwarning(
                "No COM port",
                "Select an available COM port."
            )
            return

        port = selection.split(" - ")[0]

        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=BAUD_RATE,
                timeout=0.1,
                write_timeout=1
            )

            self.running = True

            self.reader_thread = threading.Thread(
                target=self.serial_reader,
                daemon=True
            )

            self.reader_thread.start()

            self.connection_status.set(
                f"Connected: {port}"
            )

            self.connect_button.config(state="disabled")
            self.disconnect_button.config(state="normal")
            self.send_button.config(state="normal")

            self.add_log(
                "SYSTEM",
                f"Connected to ESP32 on {port}"
            )

            # ESP32 may reset when the serial port opens.
            self.root.after(1500, self.initialise_gateway)

        except Exception as error:

            messagebox.showerror(
                "Serial connection error",
                str(error)
            )

    def disconnect_serial(self):

        self.running = False

        if self.serial_port:

            try:
                self.serial_port.close()
            except Exception:
                pass

            self.serial_port = None

        self.connection_status.set("Disconnected")

        self.connect_button.config(state="normal")
        self.disconnect_button.config(state="disabled")
        self.send_button.config(state="disabled")

        self.module1_status.set("Disconnected")
        self.module2_status.set("Disconnected")

        self.add_log("SYSTEM", "Serial connection closed")

    def initialise_gateway(self):

        if not self.is_connected():
            return

        self.send_command("PING")

        self.query_configuration(1)
        self.query_configuration(2)

    def is_connected(self):

        return (
            self.serial_port is not None
            and self.serial_port.is_open
        )

    # =====================================================
    # SERIAL READER THREAD
    # =====================================================

    def serial_reader(self):

        while self.running:

            try:

                if self.serial_port is None:
                    break

                line = self.serial_port.readline()

                if line:
                    decoded = line.decode(
                        "utf-8",
                        errors="replace"
                    ).strip()

                    if decoded:
                        self.event_queue.put(decoded)

            except Exception as error:

                self.event_queue.put(
                    f"ERROR|{error}"
                )

                break

    # =====================================================
    # SERIAL COMMAND TRANSMISSION
    # =====================================================

    def send_command(self, command):

        if not self.is_connected():
            return False

        try:

            data = (command + "\n").encode("utf-8")

            self.serial_port.write(data)
            self.serial_port.flush()

            self.add_log(
                "TX",
                f"PC -> ESP32: {command}"
            )

            return True

        except Exception as error:

            self.add_log("ERROR", str(error))
            return False

    # =====================================================
    # CONFIGURATION
    # =====================================================

    def apply_configuration(self, module):

        if not self.is_connected():
            messagebox.showwarning(
                "Not connected",
                "Connect to the ESP32 first."
            )
            return

        if module == 1:
            address = self.module1_address.get().strip()
            network = self.module1_network.get().strip()
        else:
            address = self.module2_address.get().strip()
            network = self.module2_network.get().strip()

        try:

            address_value = int(address)
            network_value = int(network)

            if not 0 <= address_value <= 65535:
                raise ValueError("Address must be 0-65535.")

            if not 3 <= network_value <= 15:
                raise ValueError("Network ID must be 3-15.")

        except ValueError as error:

            messagebox.showerror(
                "Invalid configuration",
                str(error)
            )
            return

        self.send_command(
            f"CFG,{module},ADDRESS,{address_value}"
        )

        self.send_command(
            f"CFG,{module},NETWORKID,{network_value}"
        )

        self.add_log(
            "SYSTEM",
            f"Module {module} configuration commands sent"
        )

        self.root.after(
            500,
            lambda: self.query_configuration(module)
        )

    def query_configuration(self, module):

        if not self.is_connected():
            return

        self.send_command(f"QUERY,{module},ADDRESS")
        self.send_command(f"QUERY,{module},NETWORKID")
        self.send_command(f"QUERY,{module},IPR")

    # =====================================================
    # MESSAGE COMPOSER
    # =====================================================

    def update_destination(self, event=None):

        if self.selected_module.get() == "1":
            self.destination.set(
                self.module2_address.get()
            )
        else:
            self.destination.set(
                self.module1_address.get()
            )

    def update_byte_count(self, *args):

        message = self.message_text.get()
        byte_count = len(message.encode("utf-8"))

        self.byte_count.config(
            text=f"{byte_count} / {MAX_MESSAGE_BYTES} bytes"
        )

    def send_message(self):

        if not self.is_connected():
            messagebox.showwarning(
                "Not connected",
                "Connect to the ESP32 first."
            )
            return

        module = self.selected_module.get()
        destination = self.destination.get().strip()
        message = self.message_text.get()

        if not message:
            return

        try:
            destination_value = int(destination)

            if not 0 <= destination_value <= 65535:
                raise ValueError

        except ValueError:

            messagebox.showerror(
                "Invalid destination",
                "Enter a valid destination address."
            )
            return

        byte_count = len(message.encode("utf-8"))

        if byte_count > MAX_MESSAGE_BYTES:
            messagebox.showerror(
                "Message too long",
                f"Maximum payload is {MAX_MESSAGE_BYTES} bytes."
            )
            return

        if byte_count == 0:
            return

        command = (
            f"SEND,{module},{destination_value},{message}"
        )

        if self.send_command(command):

            self.add_log(
                "TX",
                f"Module {module} -> Address "
                f"{destination_value}: {message}"
            )

            self.message_text.set("")

    # =====================================================
    # PROCESS ESP32 EVENTS
    # =====================================================

    def process_events(self):

        while not self.event_queue.empty():

            try:
                line = self.event_queue.get_nowait()
            except queue.Empty:
                break

            self.process_gateway_message(line)

        self.root.after(100, self.process_events)

    def process_gateway_message(self, line):

        parts = line.split("|", 2)

        event_type = parts[0]

        if event_type == "PONG":

            self.add_log(
                "STATUS",
                "ESP32 gateway responding"
            )

        elif event_type == "STATUS":

            message = parts[1] if len(parts) > 1 else ""

            self.add_log("STATUS", message)

        elif event_type == "HEARTBEAT":

            pass

        elif event_type == "TXCMD":

            if len(parts) >= 3:

                module = parts[1]
                command = parts[2]

                self.add_log(
                    "TX",
                    f"Module {module} UART: {command}"
                )

        elif event_type == "LORA":

            if len(parts) >= 3:

                module = parts[1]
                response = parts[2]

                self.add_log(
                    "RX",
                    f"Module {module} UART: {response}"
                )

                self.process_radio_response(
                    module,
                    response
                )

        elif event_type == "ERROR":

            message = parts[1] if len(parts) > 1 else line

            self.add_log("ERROR", message)

        else:

            self.add_log("SYSTEM", line)

    # =====================================================
    # RADIO RESPONSE INTERPRETATION
    # =====================================================

    def process_radio_response(self, module, response):

        if module == "1":
            status = self.module1_status
        else:
            status = self.module2_status

        if "+OK" in response:
            status.set("Radio responding")

        elif "+ADDRESS=" in response:

            value = response.split("=", 1)[1].strip()

            if module == "1":
                self.module1_address.set(value)
            else:
                self.module2_address.set(value)

        elif "+NETWORKID=" in response:

            value = response.split("=", 1)[1].strip()

            if module == "1":
                self.module1_network.set(value)
            else:
                self.module2_network.set(value)

        elif "+IPR=" in response:

            status.set(
                f"Ready | UART baud {response.split('=')[-1]}"
            )

        elif response.startswith("+RCV="):

            self.add_log(
                "RX",
                f"*** RADIO PAYLOAD RECEIVED ON MODULE {module} ***"
            )

    # =====================================================
    # LOGGING
    # =====================================================

    def add_log(self, category, message):

        timestamp = datetime.now().strftime(
            "%H:%M:%S.%f"
        )[:-3]

        line = f"{timestamp} | {category:<6} | {message}"

        self.log_lines.append(line)

        self.log_display.config(state="normal")

        self.log_display.insert(
            "end",
            line + "\n",
            category
        )

        if self.auto_scroll.get():
            self.log_display.see("end")

        self.log_display.config(state="disabled")

    def clear_log(self):

        self.log_lines.clear()

        self.log_display.config(state="normal")
        self.log_display.delete("1.0", "end")
        self.log_display.config(state="disabled")

    def save_log(self):

        if not self.log_lines:
            messagebox.showinfo(
                "Empty log",
                "There is no communication data to save."
            )
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("Log files", "*.log"),
                ("All files", "*.*")
            ],
            initialfile="RYLR896_Communication_Log.txt"
        )

        if not filename:
            return

        try:

            with open(
                filename,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(
                    "\n".join(self.log_lines)
                )

            messagebox.showinfo(
                "Log saved",
                f"Saved communication log:\n{filename}"
            )

        except Exception as error:

            messagebox.showerror(
                "Save error",
                str(error)
            )

    # =====================================================
    # SHUTDOWN
    # =====================================================

    def close_application(self):

        self.disconnect_serial()
        self.root.destroy()


# =========================================================
# APPLICATION ENTRY POINT
# =========================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = LoRaDashboard(root)

    root.mainloop()
