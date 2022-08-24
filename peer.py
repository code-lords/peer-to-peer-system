import os
import socket
import sys
from os.path import exists
from threading import Thread


FILE_PATH = "peerFiles/"

class Peer():
    def __init__(self,peerName,peerID,maxPeers=None):
        self.peerName = peerName
        self.peerID = peerID
        if maxPeers:
            self.maxPeers = int(maxPeers)
        else:
            self.maxPeers = 2
        self.peerPort = 5000 + int(peerID)
        self.peerHost = "127.0.0.1"
        self.peers = []
        self.hashTable = {}
        self.shutdown = False
        self.connectToPeers()
        self.getBackResources()

    #getback resources
    def getBackResources(self):
        if len(self.peers) > 0:
            checkForFiles = "c" + self.peerName
            for ID in self.peers:
                peerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        
                port = 5000 + int(ID)               
                peerSocket.connect(('127.0.0.1', port))
                #sending search request
                peerSocket.sendall(checkForFiles.encode('utf-8'))
                
                #receiving from client
                fromPeer = peerSocket.recv(4096)
                fromPeer = fromPeer.decode()
                if fromPeer != "not found":
                    file_exists = exists(FILE_PATH +self.peerName+"/"+fromPeer)
                    if file_exists:
                        self.storeInHash(fromPeer,self.peerName)
            
                peerSocket.close()
        


    # client function runs the main client code 
    def client(self):
        print("****************************")
        print("\t" +self.peerName)
        print("****************************")

        clientEnter = -1
        try:
            while int(clientEnter) != 4:
                print("\n****CLIENT MENU****")
                print("1. Register a File")
                print("2. Search for a File")
                print("3. Obtain a File")
                print("4. EXIT \n")

                clientEnter = input("Enter your choice: ")

                #register a file
                if int(clientEnter) == 1:
                    if len(self.peers) == 0:
                        self.connectToPeers()

                    fileName = input("Enter filename with extension: ")
                    file_exists = exists(FILE_PATH +self.peerName+"/"+fileName)
                    if file_exists:
                        self.storeInHash(fileName,self.peerName)
                        print("\nSUCCESS, registered successfully\n")
                    else:
                        print("\nDANGER! You do not have this file on your computer\n")

                #search for a file on connected peers    
                elif int(clientEnter) == 2:
                    if len(self.peers) == 0:
                        self.connectToPeers()

                    fileName = input("Enter the File Name to be searched: ")
                    self.peersWithFile = []
                    if fileName in self.hashTable:
                        self.peersWithFile.append(self.peerName)
                    
                    searchRequest = "s" + fileName
                    if len(self.peers) > 0:
                        for ID in self.peers:
                            peerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        
                            port = 5000 + int(ID)               
                            peerSocket.connect(('127.0.0.1', port))
                            #sending search request
                            peerSocket.sendall(searchRequest.encode('utf-8'))
                            #receiving from client
                            fromPeer = peerSocket.recv(4096)
                            fromPeer = fromPeer.decode()
                            if fromPeer == "found":
                                self.peersWithFile.append("peer"+str(ID))
                            peerSocket.close()
                    print(self.peersWithFile)

                #obtain a file    
                elif int(clientEnter) == 3:
                    if len(self.peers) == 0:
                        self.connectToPeers()
                    
                    obtainFileName = input("Enter the File Name:")
                    
                    self.peersWithFile = []
                    if obtainFileName in self.hashTable:
                        print("File already on this peer")
                    elif len(self.peers) > 0:  
                        obtainPeerName = "peer"
                        searchRequest = "s" + obtainFileName
                        file_exists_here = False
                        for ID in self.peers:
                            peerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        
                            port = 5000 + int(ID)               
                            peerSocket.connect(('127.0.0.1', port))
                            #sending search request
                            peerSocket.sendall(searchRequest.encode('utf-8'))
                            #receiving from client
                            fromPeer = peerSocket.recv(4096)
                            fromPeer = fromPeer.decode()
                            if fromPeer == "found":
                                file_exists_here = True
                                obtainPeerName = obtainPeerName+str(ID)
                            peerSocket.close()

                        if file_exists_here == True:
                            obtainPeerPort = 5000 + int(obtainPeerName[-1])
                            obtainRequest = "o" + obtainFileName
                            peerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            peerSocket.connect(('127.0.0.1', obtainPeerPort))
                            peerSocket.sendall(obtainRequest.encode('utf-8'))
                            
                            file = open(FILE_PATH +self.peerName+"/"+obtainFileName, "wb")
                            print("Receiving....")
                            data = peerSocket.recv(1024)
                            file.write(data)
                            file.close()
                        else:
                            print("File not found")					
                    
                #relocation of resources
                elif int(clientEnter) == 4:
                    if len(self.peers) == 0:
                        self.connectToPeers()

                    if len(self.hashTable) > 0:
                        if len(self.peers) > 0:
                            peerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        
                            port = 5000 + int(self.peers[0])               
                            peerSocket.connect(('127.0.0.1', port))
                            for doc in self.hashTable:
                                #sending hash of file
                                hashAddRequest = "h"+self.peerName+ doc
                                peerSocket.sendall(hashAddRequest.encode('utf-8'))
                                print("Reallocating resources to peer"+str(self.peers[0]))
                            
                                #receiving response from server
                                fromPeer = peerSocket.recv(4096)
                                fromPeer = fromPeer.decode()
                                if fromPeer == "added":
                                    continue
                                else:
                                    print("An error occurred")
                            
                            peerSocket.close()
                        else:
                            print("\n DANGER! Not connected to any other peers")

                    print("THANK YOU AND GOODBYE")
                    os._exit(1)
                else:
                    print("Please choose a correct command")

        except ValueError:
            print("\nPlease enter the correct commands")
        
    #server function runs the main server code
    def server(self):
        peerServ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peerServ.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        peerServ.bind((self.peerHost, self.peerPort))
        peerServ.listen(5)
        while True:
            conn, addr = peerServ.accept()
            while True:
                incomingRequest = conn.recv(1024)
                incomingRequest = incomingRequest.decode()
                if not incomingRequest: break

                #search for a file
                if incomingRequest[0] == 's':
                    outGoingRequest = self.searchForResource(incomingRequest)
                    conn.sendall(outGoingRequest.encode('utf-8'))
                
                #obtain a file
                elif incomingRequest[0] == 'o':
                    fileToSend = open(FILE_PATH + self.hashTable[incomingRequest[1:]]+"/"+incomingRequest[1:],'rb')
                    outGoingRequest = fileToSend.read(1024)
                    conn.send(outGoingRequest)

                #store resources before leaving
                elif incomingRequest[0] == 'h':
                    self.storeInHash(incomingRequest[6:],incomingRequest[1:6])
                    outGoingRequest = "added"
                    conn.sendall(outGoingRequest.encode('utf-8'))

                #get back Resources
                elif incomingRequest[0] == 'c':
                    outGoingRequest = self.searchForResourceValue(incomingRequest)
                    conn.sendall(outGoingRequest.encode('utf-8'))
                
                else:
                    outGoingRequest = "Not found"
                    conn.sendall(outGoingRequest.encode('utf-8'))
        conn.close

    def searchForResourceValue(self, searchRequest):
        for h in self.hashTable:
            if self.hashTable[h] == searchRequest[1:]:
                fileName = h
                del self.hashTable[h]
                return fileName
        return "not found"
            
    def searchForResource(self, searchRequest):
        if searchRequest[1:] in self.hashTable:
            return "found"
        else:
            return "not"

    def storeInHash(self,key,value):
        self.hashTable[key] = value
    
    def connectToPeers(self):
        socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        x = 0
        while (x <= 3):
            checkedPort = 5000 + x
            if checkedPort == self.peerPort:
                x += 1
                continue
            checkedPortResult = is_port_in_use(checkedPort)
            if checkedPortResult:
                self.peers.append(x)
            x += 1

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

""""INITIALISES A PEER"""

peer = Peer(sys.argv[1],sys.argv[1][-1])

t1 = Thread(target = peer.server, args=( ))
t2 = Thread(target = peer.client, args=( ))

t1.start()
t2.start()



