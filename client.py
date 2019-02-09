import os
import sys
import time
import json
import socket
import pickle
import random

def init():
	global sock,max_msg_len,grid_dimension,grid,striked_positions,bingo
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	max_msg_len = 10000
	grid_dimension = 0
	grid = [[]]
	striked_positions = [[]]
	bingo = False

def load_grid(bingo_grid):
	global grid,striked,not_striked,striked_positions,bingo
	striked = []
	not_striked = [i for i in range(grid_dimension*grid_dimension)]
	striked_positions = [[False for j in range(grid_dimension)] for i in range(grid_dimension)]
	grid = bingo_grid[:]
	bingo = False
	print (grid)
	
def encode(data):
	return pickle.dumps(data)

def decode(bytes):
	return pickle.loads(bytes)

def send_ping(hostname,user_name):
	global grid_dimension
	# hostname = socket.gethostname()	#must remove this later. This is just for testing purposes
	sock.connect((hostname, 9999))
	json_obj = {"ping":True,"name":user_name}
	sock.send(encode(json_obj))
	json_obj = decode(sock.recv(max_msg_len))
	if ("ack" in json_obj):
		grid_dimension = json_obj['grid_dimension']
		return True
	else:
		print (json_obj["error"])
		return False
	
def send_grid():
	grid_accepted = False
	while (not grid_accepted):
		json_obj = decode(sock.recv(max_msg_len))
		if ("send_grid" in json_obj and json_obj["send_grid"]):
			sock.send(encode({"grid":grid}))
			response = decode(sock.recv(max_msg_len))
			if ("ack" in response):
				grid_accepted = True
			else:
				print (response["error"])

def strike_off(num):
	striked.append(num)
	not_striked.remove(num)

def recieve_moves():
	global bingo
	while (True):
		json_obj = decode(sock.recv(max_msg_len))
		if ("move" in json_obj):
			print ("{} has played {}".format(json_obj["user_name"],json_obj['move']))
			strike_off(json_obj['move'])
		if ("send_move" in json_obj):
			return
		if ("end_game" in json_obj):
			bingo = True
			if (json_obj['Victory']):
				print ("Victory!",end=" ")
			else:
				print ("Defeat",end=" ")
			print (json_obj['msg'])
			return

def send_move(move):
	json_obj = {"move":move}
	try:
		sock.send(encode(json_obj))
	except:
		print ("Banned from the game, due to many wrong moves")
		exit(0)

	response = decode(sock.recv(max_msg_len))
	if ("ack" in response):
		strike_off(move)
		print ("move {} sent".format(move))
		return True
	else:
		print (response)
		print (response['error'])
		return False

# if __name__ == "__main__":
	# init()
	# name = sys.argv[1]
	# send_ping("xyz",name)
	# make_grid()
	# send_grid()
	# # sock.send(encode(grid))
	# play_game()
	# json_obj = decode(sock.recv(1024))
