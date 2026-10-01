# import digital_pot
import struct
import math

import machine
import network
import socket
from time import sleep
from machine import SPI, Pin

led = Pin("LED", Pin.OUT)
ssid = 'Humpty'
password = '**********'

HOST = "0.0.0.0"
PORT = 22223

spi = SPI(0, baudrate=400000, polarity=0, phase=0, bits=8, firstbit=SPI.MSB, sck=Pin(2), mosi=Pin(3), miso=Pin(4))
csA = Pin(1, mode=Pin.OUT, value=1)
csB = Pin(17, mode=Pin.OUT, value=1)
out_buf = bytearray(b'\x01\x00\x00')
in_buf = bytearray(b'\x00\x00\x00')
PinsA = [0, 1, 2, 3, 4, 5, 6, 7]
PinsB = [0, 1, 2, 3, 4, 5, 6, 7]
R1 = 10000
Ta = [0.0]*16
TaLast = Ta
TaRising = [False]*16
c1 = 0.001125308852122
c2 = 0.000234711863267
c3 = 0.000000085663516
counter = 0


def connect():
    # Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    count = 0
    while not wlan.isconnected():
        print('Waiting for connection...')
        led.high()
        if count > 60:
            wlan.disconnect()
            machine.reset()
        sleep(1)
        led.low()
        sleep(1)
        count = count + 1
    led.high()
    ip = wlan.ifconfig()[0]
    print(ip)
    return ip, wlan


def open_socket():
    # Open a socket
    address = (HOST, PORT)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    conn, addr = connection.accept()
    print(f"Connected by {addr}")
    data = conn.recv(1024)
    conn.sendall(data)
    return conn


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
    ip, wlan = connect()
    led.low()
    sleep(2)
    led.high()
    conn = open_socket()
    sleep(1)
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
                    if (TaRising[i] is False) & (TaDelta < 20):
                        Ta[i] = TaLast[i]
                    else:
                        TaRising[i] = True
                else:
                    if (TaRising[i] is True) & (TaDelta > -20):
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
            # boiler flow temperature set
            # data = conn.recv(1024)
            # print(data)
            # digital_pot.POT0_Dn = digital_pot.set_dn(data)
            # digital_pot.digital_pot_write(digital_pot.POT0_SEL, digital_pot.POT0_Dn)
        for x in PinsA:
            voltage = capture(x, csA)
            temperature = convert_to_temp(voltage)
            Ta[x] += temperature
        for x in PinsB:
            voltage = capture(x, csB)
            temperature = convert_to_temp(voltage)
            Ta[x+8] += temperature
        sleep(0.3)
        counter += 1

except KeyboardInterrupt:
    print('tim\'s keyboard interrupt')

except OSError:
    print('os error')
    print('resetting')
    conn.close()
    wlan.disconnect()
    x = 0
    while x < 10:
        led.low()
        sleep(0.5)
        led.high()
        sleep(0.5)
        x = x+1
    sleep(2)
    machine.reset()
