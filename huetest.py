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
r = requests.put(hue_hub_url, json.dumps({"on":True, "sat":200, "bri":254, "hue":0}), timeout=5)

#mock pressure stats and input here
input_max = 3.5
input_min = 1.5

input = 2

#map input float to best fit in the list of hues
index = len(hue_color) - round(len(hue_color) * ((input - input_min) / (input_max - input_min)))
print (index)

#change color
color_payload = {"hue": hue_color[index]}
print(color_payload) 
r = requests.put(hue_hub_url, json.dumps(color_payload), timeout=5)
time.sleep(2)

#turn off before exiting
r = requests.put(hue_hub_url, json.dumps({"on":False}), timeout=5)
