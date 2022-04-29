#!/usr/bin/env python3

from bluedot.btcomm import BluetoothClient
from datetime import datetime
from time import sleep
from signal import pause

import Adafruit_DHT
import datetime
import sys


DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4

def getData():
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    print(str(humidity)+"\t"+str(temperature))
   

    if humidity is not None and temperature is not None:
        ct = datetime.datetime.now()
        
        return "{0:0.1f}|{1:0.1}|healthy|".format(temperature, humidity)       
        #return "Temp={0:0.1f}*C  Humidity={1:0.1f}% Timestamp={2}".format(temperature, humidity,ct )
    else:
        print("Failed to retrieve data from humidity sensor")


def data_received(data):
    print("recv - {}".format(data))

print("Connecting")
c = BluetoothClient("raspberrypi", data_received, port=1)

print("Sending")
try:
    while True:
        c.send(getData() + "\n")
        sleep(1)
finally:
    c.disconnect()
