import serial as sl
from serial.tools import list_ports_osx as list_ports

curr_str = ""
n_hit = False
r_hit = False


def query_serial_ports():
    ports = []
    for a, _, _ in list_ports.comports():
        ports.append(a)
    return ports


def connectToSerialPort(port):
    # "/dev/cu.usbmodem141301"
    try:
        ser = sl.Serial(port, 9600, timeout=0)
        return ser
    except Exception as e:
        print(e)
        return None


def close_serial_port_connection(ser):
    ser.close()


def read_serial_connection(ser):
    # bval = ser.readline()
    if not ser.isOpen():
        ser.open()
    try:
        val = ser.readline().decode("utf-8").replace(r"\r", "").replace(
            r"\n", "").strip()
        return float(val)
    except ValueError:
        return 0


if __name__ == "__main__":
    print(query_serial_ports())
    ser = connectToSerialPort('/dev/cu.Bluetooth-Incoming-Port')
    while True:
        print(read_serial_connection(ser))
