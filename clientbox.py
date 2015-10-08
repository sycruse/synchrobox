#!/usr/bin/python3
# Author: Tim 9 Jaringan Komputer C, Fasilkom Universitas Indonesia
# Dikerjakan sebagai Tugas Kelompok 3

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

		print("Finish initialize client!")
		self.connectToServer()

		self.mainProcedure()

	# =============================
	# Main procedure to be repeated
	# =============================
	def mainProcedure(self):
		self.constructFileList()
		self.sendFileList()
		self.receiveRequestList()
		self.exchangingFiles()

	# ======================
	# Synchronization family
	# ======================
	def sendFileList(self):
		print("Prepare to send encoded data of client file list..")
		encodedData = json.dumps(self.fileList)
		self.clientSocket.sendto(encodedData.encode('ascii'),self.address)
		print("Client file list sent!")
		print(self.address)

	def receiveRequestList(self):
		print("Wait to receive data from server: request for client file list..")
		data = self.clientSocket.recv(self.bufSize)
		(self.requestFileList, self.incomingFileNumber) = json.loads(data.decode('ascii'))
		print("Request file to send to server: {}".format(self.requestFileList))
		print("Incoming file number from server: {}".format(self.incomingFileNumber))

	def exchangingFiles(self):
		print("Synchronization: receiving files from server..")
		if(self.incomingFileNumber != 0):
			for index in range(0, self.incomingFileNumber):
				# Get data header
				jsonDataHeader = self.clientSocket.recv(self.bufSize).decode('ascii')
				(dataName,dataSize) = json.loads(jsonDataHeader)
				print("Receiving file: [{}] with size: [{}]".format(dataName, dataSize))

				# Get real data
				fileObject = open(dataName, 'wb')
				data = self.clientSocket.recv(self.bufSize)
				#calcDataSize += len(data)
				print("Downloading file...")
				try:
					while(data):
						fileObject.write(data)
						self.clientSocket.settimeout(2)
						data = self.clientSocket.recv(self.bufSize)
						if(data == b'eof'):
							print("End of file catched!")
							break
				except timeout:
					fileObject.close()
				print("Download finished!")
				fileObject.close()
		else:
			print("Synchronization: nothing to receive from server!")

		print("Synchronization: sending files to server..")
		if(len(self.requestFileList) != 0):
			for dataName in self.requestFileList:
				# Send data header
				dataSize = os.path.getsize(dataName)
				dataHeader = (dataName, dataSize)
				jsonDataHeader = json.dumps(dataHeader)
				self.clientSocket.send(jsonDataHeader.encode('ascii'))
				print("Sending file: [{}] with size: [{}]".format(dataName, dataSize))

				# Send real data
				count = 1
				fileObject = open(dataName, "rb")
				data = fileObject.read(self.bufSize)
				print("Sending the file...")
				while (data):
					if(self.clientSocket.send(data)):
						if(count % 1000 == 0):
							print(".")
						count += 1
						data = fileObject.read(self.bufSize)
				print("Sending end of file signal")
				self.clientSocket.send(b'eof')
				print("Finish sending file!")
		else:
			print("Synchronization: nothing to send to server!")

		# Synchronization complete
		print("Synchronization: Congratulations, you are synchronized!")

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
		print("File list construction complete!")

	def updateFileList(self):
		self.constructFileList()

	def listenForConnection(self):
		print("Client is listening....")
		self.clientSocket.listen(5)

def main():
	client = ClientBox()

if __name__ == "__main__": main()
