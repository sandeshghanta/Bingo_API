import os
import time
import json
import random
import socket
import pickle
from multiprocessing import Process

users = []
no_of_users = 1
timeout = 100
grid_dimension = 5
max_msg_len = grid_dimension*grid_dimension*10000	#must keep a more accurate later

class User:
	def __init__(self,ip_addr,clientsocket):
		self.bingo_grid = [['-' for j in range(grid_dimension)] for i in range(grid_dimension)]
		self.ip_addr = ip_addr
		self.clientsocket = clientsocket

	def load_grid(grid):
		for row_ind in range(grid_dimension):
			for col_ind in range(grid_dimension):
				self.bingo_grid[row_ind][col_ind] = grid[row_ind][col_ind]

	def validate_grid_input(grid):
		for i in range(grid_dimension*grid_dimension):
			element_found = False
			for row in grid:
				if (i in row):
					element_found = True
					break
			if (not element_found):
				print ("{} is not found in {} user's grid".format(i,self.ip_addr))
				return False
		for row in grid:
			if (len(row) != grid_dimension):
				print ("{} user's grid is invalid, expected size is {}*{}".format(self.ip_addr,grid_dimension,grid_dimension))
				return False
		if (len(grid) != grid_dimension):
			print ("{} user's grid is invalid, expected size is {}*{}".format(self.ip_addr,grid_dimension,grid_dimension))
			return False
		return True

def encode(data):
	return pickle.dumps(data)

def decode(bytes):
	return pickle.loads(bytes)

def replace_quotes(data):
	return data.replace('\'','\"')		#This is done as while the client is encoding the string the double quotes get replaced by single quotes

def listen_for_connections():
	server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	port = 9999 #making default port as 9999
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)	#To make the port reusable
	server_socket.bind((socket.gethostname(),port))
	server_socket.listen(no_of_users) #Only no_of_users can connect to server
	server_socket.settimeout(timeout)	
	print("server has started at {}".format(socket.gethostname()))
	try:
		tmp = no_of_users
		while (tmp > 0):
			print (tmp)
			clientsocket,ip_addr = server_socket.accept()
			if (ip_addr not in [user.ip_addr for user in users]):
				if (decode(clientsocket.recv(1024)) == "ping"):
					tmp = tmp - 1
					print ("{} connected".format(ip_addr))
					user = User(ip_addr,clientsocket)
					users.append(user)
					json_obj = {"grid_dimension":grid_dimension}
					user.clientsocket.send(encode(json_obj))

		server_socket.close()
	except socket.timeout:
		print ("Connection timedout, {} user's did not connect within {} seconds".format(no_of_users,timeout))
		return False
	return True

def send_all_users_message(msg):
	for user in users:
		user.clientsocket.send(encode(msg))

def get_users_grids():
	for user in users:
		grid = decode(user.clientsocket.recv(max_msg_len))
		print (grid)
		print (user)
		if (user.validate_grid_input(grid)):
			user.load_grid(grid)
		print ("grid loaded")

		
if __name__ == "__main__":
	all_connected = listen_for_connections()
	if (not all_connected):
		exit(0)
	get_users_grids()