import struct
import math

import machine
import network
import socket
from time import sleep
from machine import SPI, Pin

led = Pin("LED", Pin.OUT)
ssid = 'Humpty'
password = 'ttIImm11&&'

HOST = "0.0.0.0"
PORT = 22223  # Port to listen on (non-privileged ports are > 1023)

spi = SPI(0, baudrate=400000, polarity=0, phase=0, bits=8, firstbit=SPI.MSB, sck=Pin(2), mosi=Pin(3), miso=Pin(4))
csA = Pin(1, mode=Pin.OUT, value=1)
csB = Pin(17, mode=Pin.OUT, value=1)
out_buf = bytearray(b'\x01\x00\x00')
in_buf = bytearray(b'\x00\x00\x00')
PinsA = [0, 1, 2, 3, 4, 5, 6, 7]
PinsB = [0, 1, 2, 3, 4, 5, 6, 7]
R1 = 10000
Ta = [0.0]*16 #, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
TaLast = Ta
TaRising = [False]*16 #, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]
c1 = 0.001125308852122
c2 = 0.000234711863267
c3 = 0.000000085663516
counter = 0


def connect():
    # Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        print('Waiting for connection...')
        sleep(2)
    led.high()
    ip = wlan.ifconfig()[0]
    print(ip)
    return ip


def open_socket(ip):
    # Open a socket
    address = (HOST, PORT)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    conn, addr = connection.accept()
    print(f"Connected by {addr}")
    #    with conn:
    #        print(f"Connected by {addr}")
    # while True:
    data = conn.recv(1024)
    #print(data)
    #    if not data:
    #        break
    conn.sendall(data)
    return conn # ection


def convert_to_temp(Vo):
    if Vo is 0:
        Vo = 1
    if Vo is 1023:
        Vo = 1022
    R2 = R1 * (1023 / Vo - 1)
    logR2 = math.log(R2)
    T = (1 / (c1 + (c2 * logR2) + (c3 * logR2 * logR2 * logR2)))
    Tc = T - 273.15
    # print("temp: ", Tc)
    return Tc


def capture(pin, cs):
    try:
        out_buf[1] = (1 << 7) | (pin << 4)
        cs(0)  # Select peripheral.
        # print(out_buf)
        spi.write_readinto(out_buf, in_buf)  # Simultaneously write and read bytes.
        value = ((in_buf[1] & 0x03) << 8) | in_buf[2]
        # print("value: ", value)
    finally:
        cs(1)
    return value


try:
    led.high()
    sleep(3)
    ip = connect()
    led.low()
    sleep(1)
    led.high()
    conn = open_socket(ip)
    led.low()
    sleep(1)
    while True:
        led.high()
        if counter >= 100:
            led.low()
            counter = 0
            temperature_buf = bytearray()
            for i in range(len(Ta)):
                TaDelta = Ta[i] - TaLast[i]
                if TaDelta > 0.0:
                    if (TaRising[i] is False) & (TaDelta < 0.1):
                        Ta[i] = TaLast[i]
                    else:
                        TaRising[i] = True
                else:
                    if (TaRising[i] is True) & (TaDelta > -0.1):
                        Ta[i] = TaLast[i]
                    else:
                        TaRising[i] = False
                TaLast[i] = Ta[i]
                buf = bytearray(struct.pack("h", int(Ta[i]/10)))
                temperature_buf.extend(buf)
            print(temperature_buf)
            conn.sendall(temperature_buf)
            Ta = [0.0]*16
            sleep(3)
        for x in PinsA:
            voltage = capture(x, csA)
            temperature = convert_to_temp(voltage)
            Ta[x] += temperature
        for x in PinsB:
            voltage = capture(x, csB)
            temperature = convert_to_temp(voltage)
            Ta[x+8] += temperature
        sleep(0.1)
        counter += 1

except KeyboardInterrupt:
    print('tim\'s keyboard interrupt')

except OSError:
    print('os error')
    print('resetting')
    sleep(2)
    machine.reset()


# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#    s.bind((HOST, PORT))
#    s.listen()
#    conn, addr = s.accept()
#    with conn:
#        print(f"Connected by {addr}")
#        while True:
#           data = conn.recv(1024)
#            if not data:
#                break
#            conn.sendall(data)

