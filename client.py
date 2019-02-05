import os
import time
import socket

def send_request():
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((socket.gethostname(), 9999))
	time.sleep(5)
	s.send("Thank you for connecting")
	s.close()

if __name__ == "__main__":
	send_request()