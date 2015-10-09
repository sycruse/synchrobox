#!/usr/bin/python3
# Author: Tim 9 Jaringan Komputer C, Fasilkom Universitas Indonesia
# Dikerjakan sebagai Tugas Kelompok 3

from socket import *
import sys
import os
import glob
import json

class ServerBox:
	def __init__(self, **kwargs):
		print("Welcome to Synchrobox!")
		print("Initialize Server...")
		if(len(sys.argv) > 2):
			self.host 			= sys.argv[2]
		else:
			self.host 			= gethostbyname(gethostname()) # "localhost"
		self.port 			= 1237
		self.bufSize 		= 4096
		self.address		= (self.host, self.port)
		self.serverSocket	= socket(AF_INET, SOCK_STREAM)

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
		self.waitForConnection()
		self.handleFileListObject()		
		self.exchangingFiles()
		while True:
			self.constructFileList()
			self.waitForConnection()
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
	def waitForConnection(self):
		print('Waiting for connection...')
		(connection,clientAddress) = self.serverSocket.accept()
		print('Connected with: {}'.format(clientAddress))
		self.connection = connection
		self.clientAddress = clientAddress

	def handleFileListObject(self):
		connection = self.connection
		clientAddress = self.clientAddress 
		(data,addressRecv) = connection.recvfrom(self.bufSize)
		#print("File list undecoded {}".format(data))
		decodedFileList = json.loads(data.decode())

		# Build list that will be sent by server to client
		deliveryFileList = []
		for serverItem in self.fileList:
			(serverItemName, serverItemModtime) = serverItem
			serverItemFound = False
			for clientItem in decodedFileList:
				(clientItemName, clientItemModtime) = clientItem
				if(clientItemName == serverItemName):
					serverItemFound = True
					if(serverItemModtime > clientItemModtime):
						#print("catch 1 {} vs {}".format(serverItem, clientItem))
						deliveryFileList.append(serverItemName)
			if(serverItemFound == False):
				#print("catch 2 {}".format(serverItem))
				deliveryFileList.append(serverItemName)

		# Build list that will be sent by client to server
		requestFileList = []
		for clientItem in decodedFileList:
			(clientItemName, clientItemModtime) = clientItem
			clientItemFound = False
			for serverItem in self.fileList:
				(serverItemName, serverItemModtime) = serverItem
				if(serverItemName == clientItemName):
					clientItemFound = True
					if(clientItemModtime > serverItemModtime):
						requestFileList.append(clientItemName)
			if(clientItemFound == False):
				requestFileList.append(clientItemName)

		# list of file (from server to client) and (from client to server) is done
		print("Server will send to client: {}".format(deliveryFileList))
		print("Client will send to server: {}".format(requestFileList))

		sendData = (requestFileList, len(deliveryFileList))
		jsonEncodedData = json.dumps(sendData)
		cp1252EncodedData = jsonEncodedData.encode()
		connection.send(cp1252EncodedData)

		self.deliveryFileList = deliveryFileList
		self.requestFileList = requestFileList
		self.clientConnection = connection

	def clientReconnect(self):
		print('Waiting for connection...')
		(connection,clientAddress) = self.serverSocket.accept()
		print('Connected with: {}'.format(clientAddress))
		self.clientConnection = connection
		self.clientAddress = clientAddress

	def clientDisconnect(self):
		self.clientConnection.close()

	def exchangingFiles(self):
		print("Synchronization: sending server file to client..")
		if(len(self.deliveryFileList) != 0):
			for dataName in self.deliveryFileList:
				# Wait for client to reconnect
				self.clientReconnect()

				# Send data header
				dataSize = os.path.getsize(dataName)
				dataModtime = os.path.getmtime(dataName)
				dataActime = os.path.getatime(dataName)
				dataHeader = (dataName, dataSize, dataActime, dataModtime)
				jsonDataHeader = json.dumps(dataHeader)
				self.clientConnection.send(jsonDataHeader.encode())
				print("Sending file: [{}] with size: [{}], actime: [{}], modtime: [{}]".format(dataName, dataSize, dataActime, dataModtime))

				# Wait for confirmation:
				confirmationCode = self.clientConnection.recv(self.bufSize).decode()
				print("Confirmation code: {}".format(confirmationCode))

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
				#self.clientConnection.send(b'eof')				

				# Disconnect to client as signal of end of file
				print("Disconnect to client as signal of end of file")
				self.clientDisconnect()
				print("Finish sending file!")
		else:
			print("Synchronization: nothing to send to client!")

		print("Synchronization: receiving files from client..")
		incomingFileNumber = len(self.requestFileList)
		if(incomingFileNumber != 0):
			for index in range(0, incomingFileNumber):
				# Wait for client to reconnect
				self.clientReconnect()

				# Get data header
				jsonDataHeader = self.clientConnection.recv(self.bufSize)
				#print("Catch jsonDataHeader: {}".format(jsonDataHeader))
				decodedJsonDataHeader = jsonDataHeader.decode()
				(dataName, dataSize, dataActime, dataModtime) = json.loads(decodedJsonDataHeader)
				print("Receiving file: [{}] with size: [{}], actime: [{}], modtime: [{}]".format(dataName, dataSize, dataActime, dataModtime))

				# Send confirmation code:
				confirmationCode = 'readycode'.encode()
				self.clientConnection.send(confirmationCode)
				print("Confirmation code sent!")

				# Get real data
				fileObject = open(dataName, 'wb')
				data = self.clientConnection.recv(self.bufSize)
				print("Downloading file...")
				try:
					#eofCatched = False
					while(data):
						fileObject.write(data)
						self.clientConnection.settimeout(2)
						data = self.clientConnection.recv(self.bufSize)
						#if(data == b'eof'):
						#	print("End of file catched!")
						#	eofCatched = True
				except timeout:
					fileObject.close()
					print("Download finished through timeout!")

				# Close file to save
				fileObject.close()
				print("Download finished")

				# Disconnect to client as signal of end of file
				self.clientDisconnect()

		else:
			print("Synchronization: nothing to receive from client!")

		# Synchronization complete
		print("Synchronization: Congratulations, you are synchronized!")

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
		self.serverSocket.sendto(encodedData.encode(),self.address)

	def handleConnection(self):
		while True:
			self.connection,self.address = self.serverSocket.accept()
			print('Connected with: {}'.format(self.address))
			self.data,self.address = self.connection.recvfrom(self.bufSize)
			print("Incoming file: {}".format(self.data.strip().decode()))
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
		#c.send('Thank You for listening'.encode())
		#c.close()
	
if __name__ == "__main__": main()
