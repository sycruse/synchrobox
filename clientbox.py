#!/usr/bin/python3

from socket import *
import sys
import os
import glob

class ClientBox:
	def __init__(self, **kwargs):
		print("Initialize client...")
		self.clientSocket 		= socket(AF_INET, SOCK_STREAM)
		self.host 				= gethostname() #"localhost"
		self.port 				= 1237
		self.bufSize			= 1024
		self.address			= (self.host, self.port)
		
		print("Changing directory to: {}".format(kwargs.get('targetdir')))
		self.targetDir			= sys.argv[1]
		os.chdir(self.targetDir)

		self.connectToServer()

		print("Finish initialize client!")
		#self.sendFile('data.png')
		#self.printAllFileName()
		self.sendAllFile()

	def connectToServer(self):
		print("Make connection to {},{}".format(self.host, self.port))
		self.clientSocket.connect((self.host, self.port))

	def sendAllFile(self):
		print("Prepare to send file...")
		for file in glob.glob("*"):
			self.fileName		= file
			self.clientSocket.sendto(self.fileName.encode('ascii'), self.address)
			self.fileObject		= open(self.fileName, "rb")
			self.data 			= self.fileObject.read(self.bufSize)
			count				= 1
			while (self.data):
				if(self.clientSocket.sendto(self.data,self.address)):
					#print("[{}] Sending the file...".format(count))
					count += 1
					self.data = self.fileObject.read(self.bufSize)
			print("Finish sending file!")

		print("Closing the client socket...")
		self.clientSocket.close()

	def sendFile(self, inputFileName):
		print("Prepare to send file...")
		self.fileName		= inputFileName
		self.clientSocket.sendto(self.fileName.encode('ascii'), self.address)
		self.fileObject		= open(self.fileName, "rb")
		self.data 			= self.fileObject.read(self.bufSize)
		count				= 1
		while (self.data):
			if(self.clientSocket.sendto(self.data,self.address)):
				print("[{}] Sending the file...".format(count))
				count += 1
				self.data = self.fileObject.read(self.bufSize)
		print("Finish sending file!")

		print("Closing the client socket...")
		self.clientSocket.close()

	def printAllFileName(self):
		print("Printing all file..")
		for file in glob.glob("*"):
			print(file)

def main():
	client = ClientBox()

if __name__ == "__main__": main()
