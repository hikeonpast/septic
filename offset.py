#!/usr/bin/env python3
import time
from datetime import datetime
import signal
import sys
import statistics
import operator

#PGSQL
import psycopg2

#rolling average
from collections import deque

# PGSQL connect
conn = psycopg2.connect('dbname=test')
cur = conn.cursor()


def read_recent(conn, cur):

	#ensure that range queries work as expected
	query = "SET TIMEZONE='America/Los_angeles';"
	cur.execute(query);

	#grab last 10 minutes of samples
	query = "select pressure from stability where time >= (now() - INTERVAL '10 minute')::timestamp(0);"
	cur.execute(query)
	result = cur.fetchall()
	result_list = list(map(operator.itemgetter(0), result))
	#print(result_list)

	#basic stats on list
	mean = statistics.mean(result_list)
	stdev = statistics.pstdev(result_list)
	print("Mean:", mean)

	#lists for above, below threshold
	increase_list = []
	decrease_list = []
	#number of standard deviations
	range = 2  

	#generate sub-lists on either side of mean
	for i, val in enumerate(result_list):
		if val >= (mean + (range*stdev)):
			print(val, "greater than {}stdev".format(range))
			increase_list.append(val)
		elif val <= (mean - (range*stdev)):
			print(val, "less than {}stdev".format(range))
			decrease_list.append(val)
	
	#attempt to determine size of step change
	psi_change = 0
	if len(increase_list) > len(decrease_list):
		psi_change = statistics.mean(increase_list) - mean 
		print("looks like hose moved down by {} psi".format(psi_change))
	elif len(decrease_list) > len(increase_list):
		psi_change = mean - statistics.mean(decrease_list)
		print("looks like hose moved up by {} psi".format(psi_change))
	else:
		print("no obvious change")
	return(psi_change)

def write_offset(conn, cur, offset):
	
	#read and report current value
	query = "select value from config where key = 'hose_offset';"
	cur.execute(query)
	result = cur.fetchone()
	print("Adjusting offset from {} to {}".format(result[0], offset))

	#query = "update config set value='{}' where key='hose_offset';", offset)
	#print(query)
	
#main
psi_change = read_recent(conn, cur)
depth_change = psi_change * 27.7076

if depth_change != 0:
	write_offset(conn, cur, depth_change)
