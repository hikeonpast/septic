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

def signal_handler(sig, frame):
	print('You pressed Ctrl+C!')

	# Make the changes to the database persistent
	conn.commit()

	# Close communication with the database
	cur.close()
	conn.close()
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
	#print("Abs Pressure (amb): {:6.1f} Abs Pressure (port): {:6.1f}  Temperature: {:5.2f}".format(bmp.pressure, mpr.pressure, bmp.temperature))
	print("Port pressure (PSI): {:1.3f} Temperature: {:5.2f}".format(port, bmp.temperature))

	add_record(port, bmp.temperature, bmp.pressure)
	conn.commit()
	time.sleep(60)

