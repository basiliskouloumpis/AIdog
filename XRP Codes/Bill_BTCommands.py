
from XRPLib.defaults import *

import bluetooth
import time
import micropython

micropython.alloc_emergency_exception_buf(100)

# ==================================================
# BLE UART service UUIDs
# Nordic UART Service compatible
# ==================================================

_IRQ_CENTRAL_CONNECT = 1
_IRQ_CENTRAL_DISCONNECT = 2
_IRQ_GATTS_WRITE = 3

_FLAG_READ = 0x0002
_FLAG_WRITE = 0x0008
_FLAG_NOTIFY = 0x0010

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_READ | _FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_WRITE,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)

BLE_NAME = "XRP_DOG"


# ==================================================
# BLE UART class
# ==================================================

class BLEUART:
    def __init__(self, ble, name):
        self._ble = ble
        self._ble.active(True)

        ((self._tx_handle, self._rx_handle),) = self._ble.gatts_register_services(
            (_UART_SERVICE,)
        )

        self._connections = set()
        self._rx_buffer = ""

        self._ble.irq(self._irq)

        self._payload = self._advertising_payload(name=name)
        self._advertise()

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, addr_type, addr = data
            self._connections.add(conn_handle)
            print("BLE connected")

        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, addr_type, addr = data

            if conn_handle in self._connections:
                self._connections.remove(conn_handle)

            print("BLE disconnected")
            self._advertise()

        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data

            if value_handle == self._rx_handle:
                raw = self._ble.gatts_read(self._rx_handle)

                try:
                    text = raw.decode("utf-8").strip()
                except:
                    text = ""

                self._rx_buffer = text

    def any(self):
        return len(self._rx_buffer) > 0

    def read(self):
        text = self._rx_buffer
        self._rx_buffer = ""
        return text

    def write(self, text):
        data = text.encode("utf-8")

        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._tx_handle, data)

    def _advertise(self):
        print("Advertising as", BLE_NAME)
        self._ble.gap_advertise(100000, adv_data=self._payload)

    def _advertising_payload(self, name=None):
        payload = bytearray()

        def append(adv_type, value):
            payload.extend(bytes((len(value) + 1, adv_type)) + value)

        if name:
            append(0x09, name.encode())

        return payload


# ==================================================
# Run external file
# ==================================================

def run_file(filename):
    print("Running file:", filename)
    uart.write("Running " + filename + "\n")

    try:
        with open(filename, "r") as f:
            code = f.read()

        exec(code)

    except Exception as e:
        print("Error running file:", e)
        uart.write("Error running " + filename + "\n")


# ==================================================
# Command handling
# ==================================================

def handle_command(command):
    command = command.strip().upper()

    print("Command received:", command)
    uart.write("Command: " + command + "\n")

    if command == "CRAWL":
        run_file("Bill_CrawlGait.py")

    elif command == "STAND":
        run_file("Bill_Stand.py")
        
    elif command == "TROT":
        run_file("Bill_TrotGait.py")    

    elif command == "TEST":
        run_file("Bill_servos.py")

    elif command == "PING":
        uart.write("XRP_DOG_OK\n")

    else:
        uart.write("Unknown command\n")


# ==================================================
# Main
# ==================================================

ble = bluetooth.BLE()
uart = BLEUART(ble, BLE_NAME)

print("XRP dog Bluetooth command runner ready")
print("Waiting for BLE commands")

while True:
    if uart.any():
        cmd = uart.read()
        handle_command(cmd)

    time.sleep(0.1)