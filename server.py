import os
import time
import json
import random
import socket
import pickle
from multiprocessing import Process

users = []
no_of_users = 2
timeout = 100
grid_dimension = 5
max_retries = 5
max_msg_len = grid_dimension*grid_dimension*10000	#must keep a more accurate bound later
striked_off_numbers = []

class User:
	def __init__(self,ip_addr,clientsocket,name):
		self.grid = [['-' for j in range(grid_dimension)] for i in range(grid_dimension)]
		self.striked_positions = [[False for j in range(grid_dimension)] for i in range(grid_dimension)]
		self.ip_addr = ip_addr
		self.clientsocket = clientsocket
		self.name = name
		self.win_count = 0

	def load_grid(self,grid):
		for row_ind in range(grid_dimension):
			for col_ind in range(grid_dimension):
				self.grid[row_ind][col_ind] = grid[row_ind][col_ind]
				self.striked_positions[row_ind][col_ind] = False

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
				json_obj = decode(clientsocket.recv(1024))
				accepted,response = is_valid_response(json_obj,is_ping=True)
				if (accepted):
					tmp = tmp - 1
					print ("{} connected with ip_addr {}".format(json_obj['name'],ip_addr))
					user = User(ip_addr,clientsocket,json_obj['name'])
					users.append(user)
					response.update({"grid_dimension":grid_dimension})
					user.clientsocket.send(encode(response))
				else:
					user.clientsocket.send(encode(response))

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
				accepted,response = is_valid_response(json_obj,is_grid=True)
				if (accepted):
					if (user.validate_grid_input(json_obj['grid'])):
						valid_response = True
						user.load_grid(json_obj['grid'])
						user.clientsocket.send(encode({"ack":True}))
						print ("grid of user {} loaded".format(user.name))
					else:
						user.clientsocket.send(encode({"error":"grid is invalid"}))
				else:
					user.clientsocket.send(encode(response))
					if (count == max_retries):
						print ("removing user {} from the game due to lack of valid response".format(user.name))
						removed_users.append(user)
						break
				count = count + 1
		except Exception as e:
			print (e)
			print ("user {} did not send grid".format(user.name))
			removed_users.append(user)
	
	for user in removed_users:
		users.remove(user)
	if (len(users) <= 1):
		return False
	return True

def is_valid_move(response):
	if (response['move'] > grid_dimension*grid_dimension or response['move'] < 0):
		return False,{"error":"invalid-move"}
	if (response['move'] in striked_off_numbers):
		return False,{"error":"invalid-move"}
	return True,{"ack":True}

def is_valid_response(response,is_grid=False,is_move=False,is_ping=False):
	if (type(response) is not dict):
		return False,{"error":"response-invalid"}
	if (is_move):
		if "move" not in response or type(response['move']) is not int:
			return False,{"error":"invalid-format"}
	if (is_grid):
		if "grid" not in response or type(response['grid']) is not list:
			return False,{"error":"invalid-format"}
	if (is_ping):
		if ("ping" not in response or "name" not in response):
			return False,{"error":"invalid-format"}
	
	if (is_ping and len(response.keys()) != 2):	#Ping should have exactly two keys.
		if (response['name'] in [user.name for user in users]):
			return False,{"error":"name-unavailable"}
	if (not is_ping and len(response.keys()) != 1): #"move" and "grid" should have exactly one key
		return False,{"error":"invalid-format"}
	return True,{"ack":True}
	
def get_move(user):
	move_completed = False
	count = 0
	while (not move_completed):
		json_obj = {"send_move":True,"try":count}
		time.sleep(1)
		user.clientsocket.send(encode(json_obj))
		move = user.clientsocket.recv(max_msg_len)
		move = decode(move)
		print (move)
		accepted,response = is_valid_response(move,is_move=True)
		if (not accepted):
			user.clientsocket.send(encode(response))
		else:
			accepted,response = is_valid_move(move)
			if (not accepted):
				print ("sending ",response)
				user.clientsocket.send(encode(response))
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
					user.striked_positions[row_ind][col_ind] = True
					striked = True
					break
			if (striked):
				break

def return_winners():
	winners = []
	True_row = [True for i in range(grid_dimension)]
	for user in users:
		strike_count = 0
		for row in user.striked_positions:
			if (row == True_row):
				strike_count = strike_count + 1
		for col_ind in range(grid_dimension):
			col = [user.striked_positions[row_ind][col_ind] for row_ind in range(grid_dimension)]
			if (col == True_row):
				strike_count = strike_count + 1
	
		leading_diagonal = [user.striked_positions[ind][ind] for ind in range(grid_dimension)]
		if (leading_diagonal == True_row):
			strike_count = strike_count + 1
	
		antidiagonal = [user.striked_positions[ind][grid_dimension-ind-1] for ind in range(grid_dimension)]
		if (antidiagonal == True_row):
			strike_count = strike_count + 1
	
		if (strike_count >= grid_dimension):
			winners.append(user)
	return winners
			

def play_game():
	bingo = False
	user_index = 0
	while (not bingo):
		user = users[user_index]
		move = get_move(user)
		move.update({"user_name":user.name})
		if (move == False):
			print ("Game stopped")
			return False
		for index,user in enumerate(users):
			if (index == user_index):	#have to send "ack" message for the user who sent the move
				user.clientsocket.send(encode({"ack":True}))
			else:
				user.clientsocket.send(encode(move))
		striked_off_numbers.append(move['move'])
		update_grids(move)
		winners = return_winners()
		if (len(winners) != 0):
			message = "The winners are, " + " ".join([user.name for user in winners])
			json_obj = {"end_game":True,"msg":message}
			for user in users:
				if (user in winners):
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
	no_of_games = 10
	all_connected = listen_for_connections()
	if (not all_connected):
		exit(0)
	for game in range(no_of_games):
		striked_off_numbers = []
		time.sleep(1)
		all_sent = get_users_grids()
		if (not all_sent):
			print ("Exiting game")
			exit(0)
		random.shuffle(users)	#to randomly shuffle order
		play_game()
		display_statistics(game)