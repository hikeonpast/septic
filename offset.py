#!/usr/bin/env python3
import time
from datetime import datetime
import board
import signal
import sys

#PGSQL
import psycopg2

#rolling average
from collections import deque

# PGSQL connect
conn = psycopg2.connect('dbname=test')
cur = conn.cursor()


def read_recent():

	#ensure that range queries work as expected
	query = "SET TIMEZONE='America/Los_angeles';"
	cur.execute(query);


	query = "select time::timestamp(0), pressure from stability where time >= (now() - INTERVAL '10 minute')::timestamp(0);"
        cur.execute(query)
        result = cur.fetchone()
	print(result)


def write_offset():
	
	#read and report current value
	query = "select value from config where key = 'hose_offset';"
        cur.execute(query)
        result = cur.fetchone()
	print("Adjusting offset from {} to {}".format(result, offset)

	query = "psql test -c \"update config set value='%s' where key='hose_offset';\"", offset)
	print(query)

#main
read_recent()
