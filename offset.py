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


	query = "select pressure from stability where time >= (now() - INTERVAL '10 minute')::timestamp(0);"
	cur.execute(query)
	result = cur.fetchall()
	result_list = list(map(operator.itemgetter(0), result))
	print(result_list)
	print("Mean:", statistics.mean(result_list))
	print("Variance:", statistics.variance(result_list))

def write_offset(conn, cur, offset):
	
	#read and report current value
	query = "select value from config where key = 'hose_offset';"
	cur.execute(query)
	result = cur.fetchone()
	print("Adjusting offset from {} to {}".format(result[0], offset))

	#query = "update config set value='{}' where key='hose_offset';", offset)
	#print(query)
	
#main
read_recent(conn, cur)
write_offset(conn, cur, 0)
