import time
from tflearn.layers.estimator import regression
from tflearn.layers.core import input_data, dropout, fully_connected
from tflearn.layers.conv import conv_2d, max_pool_2d
import tensorflow as tf
import numpy as np
import tflearn
from threading import Thread
import cv2 as cv
import sys
import os
from bluedot.btcomm import BluetoothClient
from datetime import datetime
from time import sleep
from signal import pause
from sense_hat import SenseHat
import json
from script import analysis
import warnings
warnings.filterwarnings('ignore')  # suppress import warnings


def process_verify_data(filepath):
	IMG_SIZE = 50
	verifying_data = []

	img_name = filepath.split('.')[0]
	print(filepath)
	time.sleep(1)
	img = cv.imread(filepath, cv.IMREAD_COLOR)
	img = cv.resize(img, (IMG_SIZE, IMG_SIZE))
	verifying_data = [np.array(img), img_name]

	np.save('verify_data.npy', verifying_data)

	return verifying_data


def analysis():

	global AI_lock
	global plant_condition
	filepath = "./Image.jpg"
	IMG_SIZE = 50
	LR = 1e-3
	MODEL_NAME = 'leafdiseasedetection-{}-{}.model'.format(
		LR, '2conv-basic')
	os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # suppress tensorflow gpu logs

	verify_data = process_verify_data(filepath)

	str_label = "Cannot make a prediction."
	status = "Error"

	cnn = input_data(shape=[None, IMG_SIZE, IMG_SIZE, 3], name='input')

	cnn = conv_2d(cnn, 32, 3, activation='relu')
	cnn = max_pool_2d(cnn, 3)

	cnn = conv_2d(cnn, 64, 3, activation='relu')
	cnn = max_pool_2d(cnn, 3)

	cnn = conv_2d(cnn, 128, 3, activation='relu')
	cnn = max_pool_2d(cnn, 3)

	cnn = conv_2d(cnn, 32, 3, activation='relu')
	cnn = max_pool_2d(cnn, 3)

	cnn = conv_2d(cnn, 64, 3, activation='relu')
	cnn = max_pool_2d(cnn, 3)

	cnn = fully_connected(cnn, 1024, activation='relu')
	cnn = dropout(cnn, 0.8)

	cnn = fully_connected(cnn, 4, activation='softmax')
	cnn = regression(cnn, optimizer='adam', learning_rate=LR,
	                     loss='categorical_crossentropy', name='targets')

	model = tflearn.DNN(cnn, tensorboard_dir='log')

	if os.path.exists('{}.meta'.format(MODEL_NAME)):
		model.load(MODEL_NAME)
		print('Model loaded successfully.')
	else:
		print('Error: Create a model using neural_network.py first.')

	img_data, img_name = verify_data[0], verify_data[1]

	orig = img_data
	data = img_data.reshape(IMG_SIZE, IMG_SIZE, 3)

	model_out = model.predict([data])[0]

	if np.argmax(model_out) == 0:
		str_label = 'Healthy'
	elif np.argmax(model_out) == 1:
		str_label = 'Bacterial'
	elif np.argmax(model_out) == 2:
		str_label = 'Viral'
	elif np.argmax(model_out) == 3:
		str_label = 'Lateblight'

	if str_label == 'Healthy':
		status = 'Healthy'
	else:
		status = 'Unhealthy'

	result = 'Status: ' + status + '.'

	if (str_label != 'Healthy'):
		result += '\nDisease: ' + str_label + '.'
	print(result)
	AI_lock = True
	plant_condition = result
	return result


def button_click(event):
    global AI_lock

    if(AI_lock):
        AI_lock = False
        cam = cv.VideoCapture(0)

        result, image = cam.read()
        print("result")
        print(result)
        if result:
            pass
            #cv.imwrite("Image.jpg",image)

        t1 = Thread(target=analysis)
        t1.start()


#Digits are displayed in a 3x5 grid
NUMS = [1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1,  # 0
        0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0,  # 1
        1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1,  # 2
        1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1,  # 3
        1, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1,  # 4
        1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1,  # 5
        1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1,  # 6
        1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0,  # 7
        1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1,  # 8
        1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1]  # 9

# Displays a single digit (0-9)


def show_digit(val, xd, yd, r, g, b):
  offset = val * 15
  for p in range(offset, offset + 15):
    xt = p % 3
    yt = (p-offset) // 3
    sense.set_pixel(xt+xd, yt+yd, r*NUMS[p], g*NUMS[p], b*NUMS[p])

# Displays a two-digits positive number (0-99)


def display_number(val):
  abs_val = abs(val)
  tens = abs_val // 10
  ones = abs_val % 10

  #Colours will range from: Blue > Green > Yellow > Orange > Red
  #Blue:  0-9
  #Green: 10-19
  #Yellow:20-29
  #Orange:30-39
  #Red:   40-99

  #Determine colour
  if val >= 0 and val < 10:
    r = 0
    g = 0
    b = 255
    if (abs_val > 9):
        show_digit(tens, OFFSET_LEFT, OFFSET_TOP, r, g, b)
        show_digit(ones, OFFSET_LEFT+4, OFFSET_TOP, r, g, b)
    elif val > 9 and val < 20:
        r = 0
        g = 255
        b = 0
    if (abs_val > 9):
        show_digit(tens, OFFSET_LEFT, OFFSET_TOP, r, g, b)
        show_digit(ones, OFFSET_LEFT+4, OFFSET_TOP, r, g, b)
    elif val > 19 and val < 30:
        r = 255
        g = 255
        b = 0
    if (abs_val > 9):
        show_digit(tens, OFFSET_LEFT, OFFSET_TOP, r, g, b)
        show_digit(ones, OFFSET_LEFT+4, OFFSET_TOP, r, g, b)
    elif val > 29 and val < 40:
        r = 255
        g = 165
        b = 0
    if (abs_val > 9):
        show_digit(tens, OFFSET_LEFT, OFFSET_TOP, r, g, b)
        show_digit(ones, OFFSET_LEFT+4, OFFSET_TOP, r, g, b)
    elif val > 39 and val < 100:
        r = 255
        g = 0
        b = 0
    if (abs_val > 9):
        show_digit(tens, OFFSET_LEFT, OFFSET_TOP, r, g, b)
        show_digit(ones, OFFSET_LEFT+4, OFFSET_TOP, r, g, b)


def data_received(data):
    global lock
    global AI_lock
    print(data)
    lock = False
    sense.clear()
    if (lock == False):
        dataList = data.split(".")
        display_number(int(dataList[0]))
        print("recv - {}".format(dataList[0]))
        sleep(5)

    lock = True


#Provide padding to center
OFFSET_LEFT = 1
OFFSET_TOP = 2

lock = True
AI_lock = True
plant_condition = "Healthy"
# Connecting to Bluetooth Server
c = BluetoothClient("raspberrypi", data_received, port=2)
print("Connecting")

# Joystick Event listener
sense = SenseHat()
sense.stick.direction_any = button_click

# Get Simulated Data
f = open("data.json")
data = json.load(f)

# Send data to Bluetooth Server
try:
    while True:
        for dataset in data:
            c.send(str(dataset['Temp'])+"|" +
                   str(dataset['Humidity'])+"|" + plant_condition + "|")
            sleep(1)
            if (lock == True):
                #print("Lock", lock)
                display_number(int(dataset['Temp']))

finally:
    c.disconnect()
