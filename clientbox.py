#!/usr/bin/python3
# Author: Tim 9 Jaringan Komputer C, Fasilkom Universitas Indonesia
# Dikerjakan sebagai Tugas Kelompok 3

from socket import *
import sys
import os
import glob
import json
import time

class ClientBox:
	def __init__(self, **kwargs):
		print("Welcome to Synchrobox!")
		print("Initialize client...")
		self.host 				= sys.argv[2] #gethostname() #"localhost"
		self.port 				= 1237
		self.bufSize			= 4096
		self.address			= (self.host, self.port)
		
		print("Changing directory to: {}".format(sys.argv[1]))
		self.targetDir			= sys.argv[1]
		os.chdir(self.targetDir)

		print("Finish initialize client!")

		self.mainProcedure()

	# =============================
	# Main procedure to be repeated
	# =============================
	def mainProcedure(self):
		self.connectToServer()
		self.constructFileList()
		self.sendFileList()
		self.receiveRequestList()
		self.disconnectFromServer()
		self.exchangingFiles()
		while True:
			print("Wait for 5 second to begin next synchronization...")
			time.sleep(5)
			self.connectToServer()
			self.constructFileList()
			self.sendFileList()
			self.receiveRequestList()
			self.disconnectFromServer()
			self.exchangingFiles()

	# ======================
	# Synchronization family
	# ======================
	def sendFileList(self):
		print("Prepare to send encoded data of client file list..")
		encodedData = json.dumps(self.fileList)
		self.clientSocket.sendto(encodedData.encode(),self.address)
		print("Client file list sent!")
		#print(self.address)

	def receiveRequestList(self):
		print("Wait to receive data from server: request for client file list..")
		data = self.clientSocket.recv(self.bufSize)
		(self.requestFileList, self.incomingFileNumber) = json.loads(data.decode())
		print("Request file to send to server: {}".format(self.requestFileList))
		print("Incoming file number from server: {}".format(self.incomingFileNumber))

	def exchangingFiles(self):
		print("Synchronization: receiving files from server..")
		if(self.incomingFileNumber != 0):
			for index in range(0, self.incomingFileNumber):
				# Reconnect to server
				self.connectToServer()

				# Get data header
				jsonDataHeader = self.clientSocket.recv(self.bufSize)
				#print("Catch jsonDataHeader: {}".format(jsonDataHeader))
				decodedJsonDataHeader = jsonDataHeader.decode()
				(dataName, dataSize, dataActime, dataModtime) = json.loads(decodedJsonDataHeader)
				print("Receiving file: [{}] with size: [{}], actime: [{}], modtime: [{}]".format(dataName, dataSize, dataActime, dataModtime))

				# Send confirmation code:
				confirmationCode = 'readycode'.encode()
				self.clientSocket.send(confirmationCode)
				print("Confirmation code sent!")

				# Get real data
				fileObject = open(dataName, 'wb')
				data = self.clientSocket.recv(self.bufSize)
				#calcDataSize += len(data)
				print("Downloading file...")
				try:
					#eofCatched = False
					while(data):
						fileObject.write(data)
						self.clientSocket.settimeout(2)
						data = self.clientSocket.recv(self.bufSize)
						#if(data == b'eof'):
						#	print("End of file catched!")
						#	eofCatched = True						
				except timeout:
					fileObject.close()
					print("Download finished through timeout!")

				# Closing file to save
				fileObject.close()
				print("Download finished!")

				# Disconnect from server
				self.disconnectFromServer()
		else:
			print("Synchronization: nothing to receive from server!")

		print("Synchronization: sending files to server..")
		if(len(self.requestFileList) != 0):
			for dataName in self.requestFileList:
				# Reconnect to server
				self.connectToServer()

				# Send data header
				dataSize = os.path.getsize(dataName)
				dataModtime = os.path.getmtime(dataName)
				dataActime = os.path.getatime(dataName)
				dataHeader = (dataName, dataSize, dataActime, dataModtime)
				jsonDataHeader = json.dumps(dataHeader)
				self.clientSocket.send(jsonDataHeader.encode())
				print("Sending file: [{}] with size: [{}], actime: [{}], modtime: [{}]".format(dataName, dataSize, dataActime, dataModtime))

				# Wait for confirmation:
				confirmationCode = self.clientSocket.recv(self.bufSize).decode()
				print("Confirmation code: {}".format(confirmationCode))

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
				#print("Sending end of file signal")
				#self.clientSocket.send(b'eof')

				# Disconnect to client as signal of end of file
				print("Disconnect to client as signal of end of file")
				self.disconnectFromServer()
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

	# ===============
	# Unused function
	# ===============
	def sendAllFile(self):
		print("Prepare to send file...")
		for file in glob.glob("*"):
			self.connectToServer()
			self.fileName		= file
			self.clientSocket.sendto(self.fileName.encode(), self.address)
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
		self.clientSocket.sendto(self.fileName.encode(), self.address)
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
