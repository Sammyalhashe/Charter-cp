import serial as sl

try:
    ser = sl.Serial("/dev/cu.usbmodem141301", 9600)
except Exception as e:
    print(e)

curr_str = ""
n_hit = False
r_hit = False


def read_ard():
    # bval = ser.readline()
    val = ser.readline().decode("utf-8")
    # print(val)
    return float(val)

