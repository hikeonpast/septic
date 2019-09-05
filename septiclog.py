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
hue_color = [0, 1250, 2500, 3750, 5000, 8378, 10000, 12500, 15000, 18000, 20000, 21845]

#turn light on
r = requests.put(hue_hub_url, json.dumps({"on":True, "sat":200, "bri":200, "hue":0}), timeout=5)

#mock pressure stats and input here
input_max = 3.8
input_min = 2.5

def signal_handler(sig, frame):
	print('You pressed Ctrl+C!')

	# Make the changes to the database persistent
	conn.commit()

	# Close communication with the database
	cur.close()
	conn.close()

	#turn off Hue on exit
	r = requests.put(hue_hub_url, json.dumps({"on":False}), timeout=5)

	sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

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


while True:
	port = (mpr.pressure - bmp.pressure + 2) / 68.9476

	#save to Postgres
	add_record(port, bmp.temperature, bmp.pressure)
	conn.commit()

	#map input float to best fit in the list of hues
	index = len(hue_color) - round(len(hue_color) * ((port - input_min) / (input_max - input_min)))
	print("Port pressure (PSI): {:1.3f} Temperature: {:5.2f} Array Index {}".format(port, bmp.temperature, index))

	#change color
	color_payload = {"hue": hue_color[index]}
	r = requests.put(hue_hub_url, json.dumps(color_payload), timeout=5)

	time.sleep(60)

