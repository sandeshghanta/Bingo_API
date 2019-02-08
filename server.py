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
max_retries = 5
max_msg_len = grid_dimension*grid_dimension*10000	#must keep a more accurate bound later
striked_off_numbers = []

class User:
	def __init__(self,ip_addr,clientsocket,name):
		self.grid = [['-' for j in range(grid_dimension)] for i in range(grid_dimension)]
		self.strike = [[False for j in range(grid_dimension)] for i in range(grid_dimension)]
		self.ip_addr = ip_addr
		self.clientsocket = clientsocket
		self.name = name
		self.win_count = 0

	def load_grid(self,grid):
		for row_ind in range(grid_dimension):
			for col_ind in range(grid_dimension):
				self.grid[row_ind][col_ind] = grid[row_ind][col_ind]

	def validate_grid_input(self,grid):
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
			clientsocket,ip_addr = server_socket.accept()
			if (ip_addr not in [user.ip_addr for user in users]):
				accepted,error = is_valid_response(decode(clientsocket.recv(1024)),is_ping=True)
				if (accepted):
					tmp = tmp - 1
					print ("{} connected with ip_addr {}".format(response['name'],ip_addr))
					user = User(ip_addr,clientsocket,response['name'])
					users.append(user)
					json_obj = {"grid_dimension":grid_dimension}
					user.clientsocket.send(encode(json_obj))
				else:
					user.clientsocket.send(encode(error))

		server_socket.close()
	except socket.timeout:
		print ("Connection timedout, {} user's did not connect within {} seconds".format(no_of_users,timeout))
		return False
	return True

def send_all_users_message(msg):
	for user in users:
		user.clientsocket.send(encode(msg))

def get_users_grids():
	removed_users = []
	for user in users:
		try:
			valid_response = False
			count = 0
			while (not valid_response):
				user.clientsocket.send(encode({"send_grid":True,"try":count}))
				json_obj = decode(user.clientsocket.recv(max_msg_len))
				if (is_valid_response(json_obj,is_grid=True) and user.validate_grid_input(grid)):
					valid_response = True
					user.load_grid(grid)
					user.clientsocket.send(encode({"ack":True}))
					print ("grid of user {} loaded".format(user.name))
				else:
					count = count + 1
					if (count == max_retries):
						print ("user {} is not sending valid responses".format(user.name))
						removed_users.append(user)
						break
		except socket.timeout:
			print ("user {} did not send grid".format(user.name))
			removed_users.append(user)
	for user in removed_users:
		users.remove(user)
	return True

def is_valid_move(user,response):
	if (response['move'] > grid_dimension*grid_dimension or response['move'] <= 0):
		return False
	if (response['move'] in striked_off_numbers):
		return False
	return True

def is_valid_response(response,is_grid=False,is_move=False,is_ping=False):
	if (type(response) is not dict):
		return False
	if (is_grid):
		if "move" not in response or type(response['move']) is not int:
			return False,"invalid-format"
	if (is_move):
		if "grid" not in response or type(response['grid']) is not list:
			return False,"invalid-format"
	if (is_ping):
		if ("ping" not in response or "name" not in response):
			return False,"invalid-format"
	if (is_ping and len(response.keys()) != 2):	#Ping should have exactly two keys.
		if (response['name'] in [user.name for user in users]):
			return False,"name-unavailable"
	if (not is_ping and len(response.keys()) == 1): #"move" and "grid" should have exactly one key
		return False,"invalid-format"
	return True,"no-error"
	
def get_move(user):
	move_completed = False
	count = 0
	while (not move_completed):
		json_obj = {"send_move":True,"try":count}
		user.clientsocket.send(encode(json_obj))
		move = user.clientsocket.recv(max_msg_len)
		response = decode(move)
		if (not is_valid_response(response)):
			user.clientsocket.send(encode("error":"wrong-format"))
		else:
			if (not is_valid_move(user,response)):
				user.clientsocket.send(encode("error":"invalid-move"))
			else:
				break
		count = count + 1
		if (count == max_retries):
			print ("User {} has exceeded max_retries".format(user.name))
			return False
	return move


def update_grids(move):
	for user in users:
		striked = False
		for row_ind,row in enumerate(user.grid):
			for col_ind,cell in enumerate(row):
				if (cell == move['move']):
					user.strike[row_ind][col_ind] = True
					striked = True
					break
			if (striked):
				break

def return_bingo_users():
	bingo_users = []
	True_row = [True for i in range(grid_dimension)]
	for user in users:
		strike_count = 0
		for row in user.strike:
			if (row == True_row):
				strike_count = strike_count + 1
		for col_ind in range(grid_dimension):
			col = [user.strike[row_ind][col_ind] for row_ind in range(grid_dimension)]
			if (col == True_row):
				strike_count = strike_count + 1
	
		leading_diagonal = [user.strike[ind][ind] for ind in range(grid_dimension)]
		if (diagonal == True_row):
			strike_count = strike_count + 1
	
		antidiagonal = [user.strike[ind][grid_dimension-ind-1] for ind in range(grid_dimension)]
		if (antidiagonal == True_row):
			strike_count = strike_count + 1
	
		if (strike_count >= grid_dimension):
			bingo_users.append(user)
	return bingo_users
			

def play_game():
	bingo = False
	user_index = 0
	while (not bingo):
		move = get_move(users[user_index])
		move.update({"user_name":user.name})
		if (move == False):
			print ("Game stopped")
			return False
		for index,user in enumerate(users):
			if (index == user_index):	#have to send "ack" message for the user who sent the move
				user.clientsocket.send(encode("ack":True))
			else:
				user.clientsocket.send(encode(move))
		striked_off_numbers.append(move['move'])
		update_grids(move)
		bingo_users = return_bingo_users()
		if (len(bingo_users) != 0):
			message = "The winners are, " + " ".join([user.name for user in users])
			json_obj = {"end_game":True,"msg":message}
			for user in users:
				if (user in bingo_users):
					json_obj['Victory'] = True
					user.win_count = user.win_count + 1
				else:
					json_obj['Victory'] = False
				user.clientsocket.send(encode(json_obj))
			bingo = True
		user_index = (user_index + 1)%len(users)
	return True

def display_statistics(game_count):
	print ("Games played {}".format(game_count))
	for user in users:
		print ("Games won by {} are {}".format(user.name,user.win_count))
		
if __name__ == "__main__":
	no_of_games = 1000
	all_connected = listen_for_connections()
		if (not all_connected):
			exit(0)
	for game in no_of_games:
		all_sent = get_users_grids()
		if (not all_sent):
			print ("Exiting game")
			exit(0)
		random.shuffle(users)	#to randomly shuffle order
		play_game()
		display_statistics(game)