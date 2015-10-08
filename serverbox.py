#!/usr/bin/python3

from socket import *
import sys
import os
import glob
import threading
import json

class ServerBox:
	def __init__(self, **kwargs):
		print("Initialize Server...")
		self.serverSocket	= socket(AF_INET, SOCK_STREAM)
		self.host 			= gethostname() # "localhost"
		self.port 			= 1237
		self.bufSize 		= 1024
		self.address		= (self.host, self.port)

		self.targetDir		= sys.argv[1]
		os.chdir(self.targetDir)
		print("Change directory to: {}".format(sys.argv[1]))

		self.createServer()
		print("Server ready!")
		
		self.listenForConnection()
		self.mainProcedure()

	# =============================
	# Main procedure to be repeated
	# =============================
	def mainProcedure(self):
		self.constructFileList()
		self.handleFileListObject()
		self.exchangingFiles()

	# ==================================
	# Connect and Listen function family
	# ==================================
	def createServer(self):
		self.serverSocket.bind(self.address)
		print("Bind socket and start to listen on {},{}".format(self.host, self.port))

	def listenForConnection(self):
		print("Server is listening....")
		self.serverSocket.listen(5)

	# ===============================
	# Synchronization function family
	# ===============================
	def handleFileListObject(self):
		(connection,clientAddress) = self.serverSocket.accept()
		print('Connected with: {}'.format(clientAddress))
		(data,addressRecv) = connection.recvfrom(self.bufSize)
		decodedFileList = json.loads(data.decode('ascii'))
		#print(decodedFileList)

		# Build list that will be sent by server to client
		deliveryFileList = []
		for serverItem in self.fileList:
			(serverItemName, serverItemModtime) = serverItem
			serverItemFound = False
			for clientItem in decodedFileList:
				(clientItemName, clientItemModtime) = clientItem
				if(clientItemName == serverItemName):
					if(serverItemModtime > clientItemModtime):
						deliveryFileList.append(serverItemName)
						serverItemFound = True
			if(serverItemFound == False):
				deliveryFileList.append(serverItemName)

		# Build list that will be sent by client to server
		requestFileList = []
		for clientItem in decodedFileList:
			(clientItemName, clientItemModtime) = clientItem
			clientItemFound = False
			for serverItem in self.fileList:
				(serverItemName, serverItemModtime) = serverItem
				if(serverItemName == clientItemName):
					if(clientItemModtime > serverItemModtime):
						requestFileList.append(clientItemName)
						clientItemFound = True
			if(clientItemFound == False):
				requestFileList.append(clientItemName)

		# list of file (from server to client) and (from client to server) is done
		print("Server will send to client: {}".format(deliveryFileList))
		print("Client will send to server: {}".format(requestFileList))

		sendData = (requestFileList, len(deliveryFileList))
		jsonEncodedData = json.dumps(sendData)
		asciiEncodedData = jsonEncodedData.encode('ascii')
		connection.send(asciiEncodedData)

		self.deliveryFileList = deliveryFileList
		self.requestFileList = requestFileList
		self.clientConnection = connection

	def exchangingFiles(self):
		print("Synchronization: sending server file to client..")
		for dataName in self.deliveryFileList:
			# Send data header
			dataSize = os.path.getsize(dataName)
			dataHeader = (dataName, dataSize)
			jsonDataHeader = json.dumps(dataHeader)
			self.clientConnection.send(jsonDataHeader.encode('ascii'))
			print("Sending file: [{}] with size: [{}]".format(dataName, dataSize))

			# Send real data
			count = 1
			fileObject = open(dataName, "rb")
			data = fileObject.read(self.bufSize)
			print("Sending the file...")
			while (data):
				if(self.clientConnection.send(data)):
					if(count % 1000 == 0):
						print(".")
					count += 1
					data = fileObject.read(self.bufSize)
			print("Sending end of file signal")
			self.clientConnection.send(b'eof')
			print("Finish sending file!")

		print("Synchronization: receiving files from client..")
		incomingFileNumber = len(self.requestFileList)
		for index in range(0, incomingFileNumber):
			# Get data header
			jsonDataHeader = self.clientConnection.recv(self.bufSize).decode('ascii')
			(dataName,dataSize) = json.loads(jsonDataHeader)
			print("Receiving file: [{}] with size: [{}]".format(dataName, dataSize))

			# Get real data
			fileObject = open(dataName, 'wb')
			data = self.clientConnection.recv(self.bufSize)
			print("Downloading file...")
			try:
				while(data):
					fileObject.write(data)
					self.clientConnection.settimeout(2)
					data = self.clientConnection.recv(self.bufSize)
					if(data == b'eof'):
						print("End of file catched!")
						break
			except timeout:
				fileObject.close()
			print("Download finished!")
			fileObject.close()

	def constructFileList(self):
		self.fileList = []
		print("Listing all file in directory..")
		for fileName in glob.glob("*"):
			inputItem = (fileName , os.path.getmtime(fileName))
			self.fileList.append(inputItem)
		print("File list construction complete!")

	# ========================
	# Additional unused family
	# ========================
	def sendFileList(self):
		encodedData = json.dumps(self.fileList)
		self.serverSocket.sendto(encodedData.encode('ascii'),self.address)

	def handleConnection(self):
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

	def updateFileList(self):
		self.constructFileList()

def main():
	server = ServerBox()

	#while True:
		#c, addr = serverSocket.accept()
		#print ('Got connection from {}'.format(addr))
		#c.send('Thank You for listening'.encode('ascii'))
		#c.close()
	
if __name__ == "__main__": main()
