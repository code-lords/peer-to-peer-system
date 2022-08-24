from audioop import add
import os
import socket
import sys
from os.path import exists
from threading import Thread
import config

FILE_PATH = "peerFiles/"


class Peer():
    """
    A simple peer class  that contains the peer name, peer id, and max number of peers

    """

    def __init__(self, name, port):
        self.__init_sever()  # assign an ip address to the server.
        self.peer_name = name  # peer name
        self.server_port = int(port)  # server port
        self.peer_id = self.generate_peer_id()  # peer id
        self.max_peers = int(config.MAX_PEERS)  # max number of peers
        self.peers = []  # list of peers
        self.hashTable = {}  # hash table to store resources
        self.shutdown = False  # flag to shutdown the server
        self.connectToPeers()  # connect to peers
        self.claim_resources()  # check if a port is in use

    def __init_sever(self):
        """
        Assign an ip address to the server.
        First attempt to get a public ip address, then fall back to localhost.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("www.google.com", 80))
            self.serverhost = s.getsockname()[0]
            s.close()
        except:
            self.serverhost = "127.0.0.1"
            print("Internet connection error")

    def generate_peer_id(self):
        """
        Generate a peer id for the peer.
        It is simply a concatenation the peer ip address and the port number.i.e ipaddress:portnumber
        """
        return self.serverhost + ":" + str(self.server_port)

    def claim_resources(self):
        """
        Claim resources from the network. This is done when a peer joins the network.
        It gets back all the resources it had
        """
        checkForFiles = "c" + self.peer_id
        peerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if len(self.peers) > 0:  # if there are known  peers in the network
            # Peer id is ipaddress:port number.

            for peer_id in self.peers:
                peerSocket.connect(
                    (peer_id.split(":")[0], int(peer_id.split(":")[1])))
                # sending search request
                peerSocket.sendall(checkForFiles.encode('utf-8'))

                # receiving from client
                fromPeer = peerSocket.recv(4096)
                fromPeer = fromPeer.decode()
                if fromPeer != "not found":
                    file_exists = exists(
                        FILE_PATH + self.peer_name+"/"+fromPeer)
                    if file_exists:
                        self.storeInHash(fromPeer, self.peer_name)

                peerSocket.close()
        else:
            try:
                peerSocket.connect((config.HOST, config.PORT))
                # sending search request
                peerSocket.sendall(checkForFiles.encode('utf-8'))

                # receiving from client
                fromPeer = peerSocket.recv(4096)
                fromPeer = fromPeer.decode()
                if fromPeer != "not found":
                    file_exists = exists(
                        FILE_PATH + self.peer_name+"/"+fromPeer)
                    if file_exists:
                        self.storeInHash(fromPeer, self.peer_name)
            except:
                print("No peers in the network")
            peerSocket.close()

    # client function runs the main client code

    def client(self):
        print("****************************")
        print("\t" + self.peer_name)
        print("****************************")

        clientEnter = -1
        try:
            while int(clientEnter) != 4:
                print("\n****CLIENT MENU****")
                print("1. Register a File")
                print("2. Search for a File")
                print("3. Obtain a File")
                print("4. EXIT \n")
                print("5. To join a peer")

                clientEnter = input("Enter your choice: ")

                # register a file
                if int(clientEnter) == 1:
                    if len(self.peers) == 0:
                        self.connectToPeers()

                    fileName = input("Enter filename with extension: ")
                    file_exists = exists(
                        FILE_PATH + self.peer_name+"/"+fileName)
                    if file_exists:
                        self.storeInHash(fileName, self.peer_name)
                        print("\nSUCCESS, registered successfully\n")
                    else:
                        print(
                            "\nDANGER! You do not have this file on your computer\n")

                # search for a file on connected peers
                elif int(clientEnter) == 2:
                    if len(self.peers) == 0:
                        self.connectToPeers()

                    fileName = input("Enter the File Name to be searched: ")
                    self.peersWithFile = []
                    if fileName in self.hashTable:
                        self.peersWithFile.append(self.peer_name)

                    searchRequest = "s" + fileName
                    if len(self.peers) > 0:
                        for ID in self.peers:
                            peerSocket = socket.socket(
                                socket.AF_INET, socket.SOCK_STREAM)
                            port = 5000 + int(ID)
                            peerSocket.connect(('127.0.0.1', port))
                            # sending search request
                            peerSocket.sendall(searchRequest.encode('utf-8'))
                            # receiving from client
                            fromPeer = peerSocket.recv(4096)
                            fromPeer = fromPeer.decode()
                            if fromPeer == "found":
                                self.peersWithFile.append("peer"+str(ID))
                            peerSocket.close()
                    print(self.peersWithFile)

                # obtain a file
                elif int(clientEnter) == 3:
                    if len(self.peers) == 0:
                        self.connectToPeers()

                    obtainFileName = input("Enter the File Name:")

                    self.peersWithFile = []
                    if obtainFileName in self.hashTable:
                        print("File already on this peer")
                    elif len(self.peers) > 0:
                        obtainpeer_name = "peer"
                        searchRequest = "s" + obtainFileName
                        file_exists_here = False
                        for ID in self.peers:
                            peerSocket = socket.socket(
                                socket.AF_INET, socket.SOCK_STREAM)
                            port = 5000 + int(ID)
                            peerSocket.connect(('127.0.0.1', port))
                            # sending search request
                            peerSocket.sendall(searchRequest.encode('utf-8'))
                            # receiving from client
                            fromPeer = peerSocket.recv(4096)
                            fromPeer = fromPeer.decode()
                            if fromPeer == "found":
                                file_exists_here = True
                                obtainpeer_name = obtainpeer_name+str(ID)
                            peerSocket.close()

                        if file_exists_here == True:
                            obtainserver_port = 5000 + int(obtainpeer_name[-1])
                            obtainRequest = "o" + obtainFileName
                            peerSocket = socket.socket(
                                socket.AF_INET, socket.SOCK_STREAM)
                            peerSocket.connect(
                                ('127.0.0.1', obtainserver_port))
                            peerSocket.sendall(obtainRequest.encode('utf-8'))

                            file = open(FILE_PATH + self.peer_name +
                                        "/"+obtainFileName, "wb")
                            print("Receiving....")
                            data = peerSocket.recv(1024)
                            file.write(data)
                            file.close()
                        else:
                            print("File not found")

                # relocation of resources
                elif int(clientEnter) == 4:
                    if len(self.peers) == 0:
                        self.connectToPeers()

                    if len(self.hashTable) > 0:
                        if len(self.peers) > 0:
                            peerSocket = socket.socket(
                                socket.AF_INET, socket.SOCK_STREAM)
                            port = 5000 + int(self.peers[0])
                            peerSocket.connect(('127.0.0.1', port))
                            for doc in self.hashTable:
                                # sending hash of file
                                hashAddRequest = "h"+self.peer_name + doc
                                peerSocket.sendall(
                                    hashAddRequest.encode('utf-8'))
                                print("Reallocating resources to peer" +
                                      str(self.peers[0]))

                                # receiving response from server
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
                elif int(clientEnter) == 5:  # Joining the network
                    peerSocket = socket.socket(
                        socket.AF_INET, socket.SOCK_STREAM)

                    peerSocket.connect((config.HOST, config.PORT))
                    # sending hash of file
                    join_request = "j"+self.peer_id  # Send the peer id to join the network
                    peerSocket.sendall(
                        join_request.encode('utf-8'))
                    # receiving response from server
                    response = peerSocket.recv(4096)
                    response = response.decode()
                    # if response == "added":
                    self.peers = self.peers + list(response)
                    print("Response from server: " + response)
                    print("\nSuccessfully joined the network\n")
                    peerSocket.close()

                else:
                    print("Please choose a correct command")

        except ValueError:
            print("\nPlease enter the correct commands")

    def listenToClient(self, client, address):
        addr, port = address
        size = 1024
        while True:
            try:
                incomingRequest = client.recv(1024)
                incomingRequest = incomingRequest.decode()
                if not incomingRequest:
                    break

                # search for a file
                if incomingRequest[0] == "j":
                    peer_id = incomingRequest[1:]
                    if peer_id not in self.peers:
                        self.peers.append(peer_id)
                        self.hashTable = self.hashTable + \
                            self.hashTable[peer_id]
                    else:
                        print("\nYou are already in the network\n")
                    outGoingRequest = self.peers
                    client.sendall(str(outGoingRequest).encode('utf-8'))

                elif incomingRequest[0] == 's':
                    outGoingRequest = self.searchForResource(incomingRequest)
                    client.sendall(outGoingRequest.encode('utf-8'))

                # obtain a file
                elif incomingRequest[0] == 'o':
                    fileToSend = open(
                        FILE_PATH + self.hashTable[incomingRequest[1:]]+"/"+incomingRequest[1:], 'rb')
                    outGoingRequest = fileToSend.read(1024)
                    client.send(outGoingRequest)

                # store resources before leaving
                elif incomingRequest[0] == 'h':
                    self.storeInHash(incomingRequest[6:], incomingRequest[1:6])
                    outGoingRequest = "added"
                    client.sendall(outGoingRequest.encode('utf-8'))

                # get back Resources
                elif incomingRequest[0] == 'c':
                    outGoingRequest = self.searchForResourceValue(
                        incomingRequest)
                    client.sendall(outGoingRequest.encode('utf-8'))

                else:
                    outGoingRequest = "Not found"
                    client.sendall(outGoingRequest.encode('utf-8'))
            except:
                client.close()
                return False

    # server function runs the main server code

    def server(self):
        peerServ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peerServ.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        peerServ.bind((self.serverhost, self.server_port))
        peerServ.listen(5)
        print(f"Started srver  ( { self.serverhost }:{self.server_port} )")
        while True:
            client, address = peerServ.accept()
            client.settimeout(60)
            Thread(target=self.listenToClient, args=(client, address)).start()

            # conn, (addr, port) = peerServ.accept()

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

    def storeInHash(self, key, value):
        self.hashTable[key] = value

    def connectToPeers(self):
        socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        x = 0
        while (x <= 3):
            checkedPort = 5000 + x
            if checkedPort == self.server_port:
                x += 1
                continue
            checkedPortResult = is_port_in_use(checkedPort)
            if checkedPortResult:
                self.peers.append(x)
            x += 1


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


if __name__ == '__main__':
    if(len(sys.argv) != 3):
        print("\nUsage : python3 %s <peer_name> <server_port>" % sys.argv[0])
        os._exit(1)
    peer = Peer(sys.argv[1], sys.argv[2])
    t1 = Thread(target=peer.server, args=())
    t2 = Thread(target=peer.client, args=())
    t1.start()
    t2.start()
