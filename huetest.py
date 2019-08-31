#!/usr/bin/env python3
import time
from datetime import datetime
import board
import signal
import sys

#used for Hue light control
import requests
import json

#includes username and ID of target light
hue_hub_url = "http://192.168.1.84/api/XYNHOn3SOzXzZbhLpKBV2xlA5d9G9CeMcKQbt9oh/lights/26/state"
hue_color = [0, 1250, 2500, 3750, 5000, 8378, 10000, 12500, 15000, 18000, 20000, 21845] 

#turn light on
r = requests.put(hue_hub_url, json.dumps({"on":True, "sat":254, "bri":254, "hue":8378}), timeout=5)

for x in hue_color:
	color_payload = {"hue": x}
	print(color_payload) 
	r = requests.put(hue_hub_url, json.dumps(color_payload), timeout=5)
	time.sleep(2)

#turn off before exiting
r = requests.put(hue_hub_url, json.dumps({"on":False}), timeout=5)
