#!/usr/bin/env python3
import time
from datetime import datetime
import board
import signal
import sys

#sensor boards
import busio
import adafruit_bmp3xx
import adafruit_mprls

#PGSQL
import psycopg2

#used for Hue light control
import requests
import json

#init stuff starts here
# I2C setup
i2c = busio.I2C(board.SCL, board.SDA)
bmp = adafruit_bmp3xx.BMP3XX_I2C(i2c)
mpr = adafruit_mprls.MPRLS(i2c, psi_min=0, psi_max=25)

#sensor setup
bmp.pressure_oversampling = 8
bmp.temperature_oversampling = 2

# PGSQL connect
conn = psycopg2.connect('dbname=test')
cur = conn.cursor()

#static vars for Hue control; URL includes username and ID of target light
hue_hub_url = "http://192.168.1.84/api/XYNHOn3SOzXzZbhLpKBV2xlA5d9G9CeMcKQbt9oh/lights/26/state"

def signal_handler(sig, frame):
	print('Graceful Exit')

	# Make the changes to the database persistent
	conn.commit()

	# Close communication with the database
	cur.close()
	conn.close()

	#turn off Hue on exit
	r = requests.put(hue_hub_url, json.dumps({"on":False}), timeout=5)

	sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

#write a database record
def add_record(press, temp, abs):

	#current time
	dt = datetime.now()

	query = """
	INSERT INTO
		stability (time, pressure, temperature, abs_press)
	VALUES 
		(%s, %s, %s, %s);
	"""
	values = (dt, press, temp, abs)
	cur.execute(query, values)
	conn.commit()


#write update to Hue 
def update_hue(press, temp):

	#static vars
	input_max = 3.7
	input_min = 2.5
	hue_color_min = 0
	hue_color_max = 21845
	#hue_color = [0, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000, 15000, 16000, 17000, 17500, 18000, 18500, 19000, 19500, 20000, 20500, 21000, 21845]
	bright_max = 255
	bright_min = 75

	#save for debug printing 
	orig_press = press
	
	#get current time and convert to brightness
	dt = datetime.now()
	hour = dt.hour
	minute = dt.minute
	if hour in range(6,20):
		if hour == 6:
			brightness = int(bright_min + (((minute + 1) / 60) * (bright_max - bright_min)))
			#print("Brightening.  Brightness: {}  Hour: {}  Min: {}".format(brightness, hour, minute))
		else:
			brightness = bright_max
			#print("Daytime")
	else:
		if hour == 20:
			brightness = int(bright_max - (((minute + 1) / 60) * (bright_max - bright_min)))
			#print("Dimming.  Brightness: {}  Hour: {}  Min: {}".format(brightness, hour, minute))
		else: 
			brightness = bright_min
			#print("Night time")

	#convert current pressure to hue color
	if press > input_max:
		press = input_max
	if press < input_min:
		press = input_min
	hue_color = hue_color_max - round((hue_color_max - hue_color_min) * ((press - input_min) / (input_max - input_min)))

	#write update
	hue_payload = {"on":True, "sat":255, "hue": hue_color, "bri": brightness}
	r = requests.put(hue_hub_url, json.dumps(hue_payload), timeout=5)
	
	#debugging is fun
	print("Port pressure (PSI): {:1.3f} Temperature: {:5.2f} Hue Color {} Brightness {:2.1f}%".format(orig_press, temp, hue_color, brightness*100/255))


while True:
	#read update from both pressure sensors and compute psi on input port
	port = (mpr.pressure - bmp.pressure + 2) / 68.9476

	#offset
	port += 1.0

	#save to Postgres
	add_record(port, bmp.temperature, bmp.pressure)

	#update hue color and brightness
	update_hue(port, bmp.temperature)

	#TODO replace with time-based mechanism so that application restarts don't write multiple records per timeslice
	time.sleep(60)

