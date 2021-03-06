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

	#commit database writes and turn off hue light
	shutdown()

	sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def shutdown():
	# Make the changes to the database persistent
        conn.commit()

        # Close communication with the database
        cur.close()
        conn.close()

        #turn off Hue on exit
        r = requests.put(hue_hub_url, json.dumps({"on":False}), timeout=5)


#write a database record
def add_record(press, temp, abs):

	#current time
	dt = datetime.now()

	query = """
	INSERT INTO
		stability (time, pressure, temperature, abs_press)
	VALUES 
		(now(), %s, %s, %s);
	"""
	values = (press, temp, abs)
	cur.execute(query, values)
	conn.commit()


#read hose offset from config table
def get_pressure_offset():

	query = "select value from config where key = 'hose_offset';"
	cur.execute(query)
	result = cur.fetchone()
	offset_inches = float(result[0])
	if (offset_inches > -24.0) and (offset_inches < 48.0):
		offset_psi = offset_inches * 0.0360912
	else:
		offset_psi = 0
	return(offset_psi)

#write update to Hue 
def update_hue(press, press_nonadj, temp):

	#static vars
	input_max = 4.3 
	input_min = 3.0
	hue_color_min = 0
	hue_color_max = 21845
	bright_max = 255
	bright_min = 65

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

	hue_color = 0
	#flag unusually low pressure with blue color
	if press < (input_min * 0.95):
		hue_color = 46920  
	#bounds checking for linear mapping
	if press > input_max:
                press = input_max
	if press < input_min:
		press = input_min
	
	#linear mapping if color not set due to special conditions
	if (hue_color == 0):
		hue_color = hue_color_max - round((hue_color_max - hue_color_min) * ((press - input_min) / (input_max - input_min)))

	#write update
	hue_payload = {"on":True, "sat":255, "hue": hue_color, "bri": brightness}

	try:
		r = requests.put(hue_hub_url, json.dumps(hue_payload), timeout=5)
	except: 
		print ("HTTP error; retrying")
	
	#debugging is fun
	print("{} - Press(adj):{:1.3f} Press(orig):{:1.3f} Temp:{:5.2f} Color:{:5.0f}".format(dt.strftime("%x %H:%M:%S"), orig_press, press_nonadj, temp, hue_color))




while True:
	#read update from both pressure sensors and compute psi on input port
	raw_press=0.0
	loops=58  #can't be more than 60
	for x in range(1,loops+1):
		raw_press += (mpr.pressure - bmp.pressure + 2) 
		time.sleep(1)
	raw_press = raw_press/loops

	#convert to PSI	
	port = raw_press / 68.9476

	#get hose offset
	hose_offset = get_pressure_offset()

	#update hue color and brightness - args are: adjusted_pressure, raw_pressure, temperature
	update_hue(port + hose_offset, port, bmp.temperature)

	#save to Postgres
	add_record(port + hose_offset, bmp.temperature, bmp.pressure)

	#TODO replace with time-based mechanism so that application restarts don't write multiple records per timeslice
	#takes a couple of seconds to do database writes
	time.sleep(60-loops-2)

