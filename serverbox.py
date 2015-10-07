#!/usr/bin/python3

from socket import *
import sys
import os
import glob

class ServerBox:
	def __init__(self, **kwargs):
		print("Initialize Server...")
		self.serverSocket	= socket(AF_INET, SOCK_STREAM)
		self.host 			= gethostname() # "localhost"
		self.port 			= 1237
		self.bufSize 		= 1024
		self.address		= (self.host, self.port)

		print("Changing directory to: {}".format(sys.argv[1]))
		self.targetDir		= sys.argv[1]
		os.chdir(self.targetDir)

		self.createServer()

		print("Server ready and listening...")
		self.listen()

	def createServer(self):
		print("Binding socket and start to listen..")
		self.serverSocket.bind(self.address)
		self.serverSocket.listen(5)

	def listen(self):
		while True:
			self.connection,self.address = self.serverSocket.accept()
			print('Connected with: {}'.format(self.address))
			self.data,self.address = self.connection.recvfrom(self.bufSize)
			print("Incoming file: {}".format(self.data.strip().decode('ascii')))
			self.fileObject = open(self.data.strip(), 'wb')
			self.data,self.address = self.connection.recvfrom(self.bufSize)
			print("Downloading file...")
			try:
				while(self.data):
					self.fileObject.write(self.data)
					self.connection.settimeout(2)
					self.data,self.address = self.connection.recvfrom(self.bufSize)
			except timeout:
				self.fileObject.close()
				self.connection.close()
			print("Download finished!")
			self.fileObject.close()
		self.connection.close()

def main():
	server = ServerBox()

	#while True:
		#c, addr = serverSocket.accept()
		#print ('Got connection from {}'.format(addr))
		#c.send('Thank You for listening'.encode('ascii'))
		#c.close()
	
if __name__ == "__main__": main()
