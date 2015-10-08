#!/usr/bin/python3

from socket import *
import sys
import os
import glob
import json

class ClientBox:
	def __init__(self, **kwargs):
		print("Initialize client...")
		self.host 				= gethostname() #"localhost"
		self.port 				= 1237
		self.bufSize			= 1024
		self.address			= (self.host, self.port)
		
		print("Changing directory to: {}".format(sys.argv[1]))
		self.targetDir			= sys.argv[1]
		os.chdir(self.targetDir)

		self.constructFileList()
		print("Finish initialize client!")

		self.connectToServer()
		self.sendFileList()
		self.receiveRequestList()

		#self.sendAllFile()

	def listenForConnection(self):
		print("Client is listening....")
		self.clientSocket.listen(5)

	def sendFileList(self):
		print("Prepare to send encoded data of client file list..")
		encodedData = json.dumps(self.fileList)
		self.clientSocket.sendto(encodedData.encode('ascii'),self.address)
		print("Client file list sent!")
		print(self.address)

	def receiveRequestList(self):
		print("Wait to receive data from server: request for client file list..")
		#self.listenForConnection()
		#(connection,address) = self.clientSocket.accept()
		data = self.clientSocket.recv(self.bufSize)
		decodedData = json.loads(data.decode('ascii'))
		print("Request file to send to server: {}".format(decodedData))

	# ======================================
	# Connect and Disconnect function family
	# ======================================
	def connectToServer(self):
		self.clientSocket		= socket(AF_INET, SOCK_STREAM)
		print("Make connection to {},{}".format(self.host, self.port))
		self.clientSocket.connect((self.host, self.port))

	def disconnectFromServer(self):
		self.clientSocket.close()

	def sendAllFile(self):
		print("Prepare to send file...")
		for file in glob.glob("*"):
			self.connectToServer()
			self.fileName		= file
			self.clientSocket.sendto(self.fileName.encode('ascii'), self.address)
			self.fileObject		= open(self.fileName, "rb")
			count				= 1

			self.data 			= self.fileObject.read(self.bufSize)
			print("Sending the file...", end="")
			while (self.data):
				if(self.clientSocket.sendto(self.data,self.address)):
					if(count % 1000 == 0):
						print(".")
					count += 1
					self.data = self.fileObject.read(self.bufSize)
			print("\nFinish sending file!")

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

	def constructFileList(self):
		self.fileList = []
		print("Listing all file in directory..")
		for fileName in glob.glob("*"):
			inputItem = (fileName , os.path.getmtime(fileName))
			self.fileList.append(inputItem)
		#print(self.fileList)

	def updateFileList(self):
		self.constructFileList()

def main():
	client = ClientBox()

if __name__ == "__main__": main()
