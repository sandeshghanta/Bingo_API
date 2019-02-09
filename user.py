import os
import random
import socket
import sys
import client

def make_grid(grid_dimension):
    #This function generates a random grid.
    grid = [[0 for j in range(grid_dimension)] for i in range(grid_dimension)]
    elements = [i for i in range(grid_dimension*grid_dimension)]
    random.shuffle(elements)
    for row_ind in range(grid_dimension):
        for col_ind in range(grid_dimension):
            element = random.choice(elements)
            grid[row_ind][col_ind] = element
            elements.remove(element)
    return grid

def get_move(striked,not_striked,grid,striked_positions,grid_dimension):
    #striked is a list numbers which have been striked off till now.
    #notstriked is a list of numbers which have not been striked off till now.
    #grid is a 2d list in which grid[i][j] contains the element which is present in i'th row and j'th col (0-based indexing)
    #striked_positions is a 2d list in which if striked_positions[i][j] is True, it means that position is striked off
    #grid_dimension is the dimension of the grid
    #[imp]You can modify the variables as you like, this will not affect the copy stored in the client.
    #[imp]Return an integer in the range [0,grid_dimension*grid_dimension) which has not been striked off till now.
    return random.choice(not_striked)


if __name__ == "__main__":
    client.init()
    result = False
    while (not result):
        hostname = str(input("Enter hostname "))
        name = str(input("Enter user_name "))
        name = sys.argv[1]
        result = client.send_ping(hostname,name)

    no_of_games = 10
    for game in range(no_of_games):
        client.load_grid(make_grid(client.grid_dimension))
        client.send_grid()
        while (not client.bingo):
            client.recieve_moves()
            if (client.bingo):
                continue
            move_sent = False
            while (not move_sent):
                move = get_move(client.striked[:],client.not_striked[:],client.grid[:],client.striked_positions[:],client.grid_dimension)
                move_sent = client.send_move(move)
                if (not move_sent):
                    client.recieve_moves()  #After the client sends a wrong move, the server again requests him to send a move, this method is used to capture that request
    print ("All games done!")