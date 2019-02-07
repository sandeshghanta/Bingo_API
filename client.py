import os
import time
import json
import socket
import pickle
import random

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def make_grid(grid_dimension):
	grid = [[j for j in range(i*grid_dimension,(i+1)*grid_dimension)] for i in range(grid_dimension)]
	return grid
	
def encode(data):
	return pickle.dumps(data)

def decode(bytes):
	return pickle.loads(bytes)

def replace_quotes(data):
	return data.replace('\'','\"')		#This is done as while the client is encoding the string the double quotes get replaced by single quotes

def send_ping():
	sock.connect((socket.gethostname(), 9999))
	sock.send(encode("ping"))
	json_obj = decode(sock.recv(1024))
	return json_obj['grid_dimension']

if __name__ == "__main__":
	grid_dimension = send_ping()
	grid = make_grid(grid_dimension)
	sock.send(encode(grid))