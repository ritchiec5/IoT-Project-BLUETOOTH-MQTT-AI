from bluedot.btcomm import BluetoothServer
from time import sleep
from signal import pause
from threading import Thread
import paho.mqtt.client as mqtt
import json
from queue import Empty, Queue
import telebot

THINGSBOARD_HOST = 'thingsboard.cloud'
ACCESS_TOKEN = 'Vjw8pXCBzQVugdmgSfsc'

#API KEY for telegram bot
API_KEY = "5200332280:AAHIL4_0vb1sAo5PxI4yzT1BGJkTh21T4Y0"
#Receiver ID to recieve telegram bot messages
#RecieverIDs = [850032350,732057751]
RecieverIDs = [850032350]
##initialize telegram bot
bot = telebot.TeleBot(API_KEY)
temperatureLimit = 30
humidityLimit = 0

lock = 0
q = []

def alertUser(id, temp, humidity):
    sensorExceed = False
    alertMessage =""
    if(float(temp)>temperatureLimit):
        alertMessage+="\nCurrent Temp = "+temp
        sensorExceed=True
    if(float(humidity)>humidityLimit):
        alertMessage+="\nCurrent Humidity = "+humidity
        sensorExceed =True
    print(alertMessage)

    if(sensorExceed):
        for receiverID in RecieverIDs:
            bot.send_message(receiverID, "Alert message from Number"+str(id)+" \n"+alertMessage)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, rc, *extra_params):
    #print('Connected with result code ' + str(rc))
    # Subscribing to receive Downlink requests
    client.subscribe('v1/devices/me/rpc/request/+')

# The callback when client connect through bluetooth
def client_connected():
    print("client connected")

# The callback when client disconnect through bluetooth
def client_disconnected():
    print("client disconnected")

# MAIN METHOD
def server_main(server_port, id):
    #q = Queue()
    sensor_data = {'id': 'sensor'+str(id), 
                    'Sensor'+str(id) + ' Temperature': 0, 
                    'Sensor'+str(id)+' humidity': 0,
                    'Sensor'+str(id)+' Plant_Condition': "NULL", }

    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
        global lock
        global q
        
        if len(q) > 0:
            q.pop()
        print('Topic: ' + msg.topic + '\nMessage: ' + str(msg.payload))
        # Decode JSON request
        data = json.loads(msg.payload)
        # Put data in queue to send to slave node
        if data['method'] == 'setSensor1':
            lock = 1
            q.append(str(data['params']))
            print(data['params'], "parameter printed")
        elif data['method'] == 'setSensor2':
            lock = 2
            q.append(str(data['params']))
            print(data['params'], "parameter printed")
        elif data['method'] == 'setSensor3':
            lock = 3
            print("sensor3:" + str(q))
            q.append(str(data['params']))
            #server.send(str(data['params']))
            #q.put(data['params'])
            print(data['params'], "parameter printed")
        print(lock)

    # The callback for bluetooth data received.
    def data_received(data):
        # Split data received into temperature and humidity
        data_list = data.split("|")

        # Send to mqtt (TEMPERATURE, HUMIDITY and PLANT CONDITION)
        sensor_data['Sensor '+str(id)+' Temperature'] = data_list[0]
        sensor_data['Sensor '+str(id)+' humidity'] = data_list[1]
        sensor_data['Sensor '+str(id)+' Plant_Condition'] = data_list[2]
        alertUser(id, data_list[0], data_list[1])
        client.publish('v1/devices/me/telemetry', json.dumps(sensor_data), 1)
        print("recv - {}".format(data))

    # BLUETOOTH INITIALIZATION
    print("Starting bluetooth server")
    server = BluetoothServer(
        data_received,
        port=server_port,
        auto_start=False,
        when_client_connects=client_connected,
        when_client_disconnects=client_disconnected)

    server.start()
    print(server.server_address)
    print("Waiting for Connection")

    # MQTT INITIALIZATION
    client = mqtt.Client()

    # Register connect callback
    client.on_connect = on_connect

    # Registed publish message callback
    client.on_message = on_message

    # Set access token
    client.username_pw_set(ACCESS_TOKEN)
    # Connect to ThingsBoard using default MQTT port and 60 seconds keepalive interval
    client.connect(THINGSBOARD_HOST, 1883, 60)

    while True:
        global lock
        global q
        '''Start MQTT Loop'''
        client.loop_start()
        if(id == lock):
            print(id, "aaa", lock)
            while len(q)>0:
                print(q[0])
                server.send(q[0])
                q.pop()
        client.loop_stop()

# Create new threads
t1 = Thread(target=server_main, args=(1, 1, ))
t2 = Thread(target=server_main, args=(2, 2, ))
t3 = Thread(target=server_main, args=(4, 3, ))

# Start new Threads
t1.start()
t2.start()
t3.start()
