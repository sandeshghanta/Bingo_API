import os
import time
import random
import socket
from multiprocessing import Process

clients = []
no_of_users = 1
timeout = 100
size_of_grid = 5

class User:
	def __init__(self,ip_addr):
		self.bingo_grid = [['-' for j in range(size_of_grid)] for i in range(size_of_grid)]
		self.ip_addr = ip_addr

	def load_grid(grid):
		for row_ind in range(size_of_grid):
			for col_ind in range(size_of_grid):
				self.bingo_grid[row_ind][col_ind] = grid[row_ind][col_ind]

	def validate_grid_input(grid):
		for i in range(size_of_grid*size_of_grid):
			element_found = False
			for row in grid:
				if (i in row):
					element_found = True
					break
			if (not element_found):
				print ("{} is not found in {} user's grid".format(i,self.ip_addr))
				return False
		for row in grid:
			if (len(row) != size_of_grid):
				print ("{} user's grid is invalid, expected size is {}*{}".format(self.ip_addr,size_of_grid,size_of_grid))
				return False
		if (len(grid) != size_of_grid):
			print ("{} user's grid is invalid, expected size is {}*{}".format(self.ip_addr,size_of_grid,size_of_grid))
			return False
		return True

def listen_for_connections():
	server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	port = 9999 #making default port as 9999
	server_socket.bind((socket.gethostname(),port))
	server_socket.listen(no_of_users) #Only no_of_users can connect to server
	server_socket.settimeout(timeout)	
	print("server has started at {}".format(socket.gethostname()))
	try:
		tmp = no_of_users
		while (tmp > 0):
			print (tmp)
			clientsocket,addr = server_socket.accept()
			if (addr not in clients):
				tmp = tmp - 1
				print ("{} connected".format(addr))
				clients.append(addr)

	except socket.timeout:
		print ("Connection timedout, {} user's did not connect within {} seconds".format(no_of_users,timeout))
		return False
	return server_socket,True

def listen_for_input_from_client(server_socket):
	print (server_socket.recv(1024))

if __name__ == "__main__":
	server_socket,all_connected = listen_for_connections()
	if (not all_connected):
		exit(0)
	#print ("All clients connected {}".format(" ".join(clients)))
	listen_for_input_from_client(server_socket)
