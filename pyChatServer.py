#!/usr/bin/python3 
import socket
import json
import select
import re

class Server:


        def __init__(self):
                self.readList, self.writeList, self.rList, self.wList = [], [], [], []
                self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.serversocket.setblocking(0)
                self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.host = '192.168.0.104' #socket.gethostname()#'192.168.0.104'
                self.port = 9000 #12345
                self.serversocket.bind((self.host, self.port))
                self.serversocket.listen(5) # Max 5 connections
                self.rList.append(self.serversocket)
                self.clientList = [] # NICKNAMES
                self.socketList = []
                self.socketList.append(self.serversocket)
                self.server()
        
        def server(self):
                print("Listening for connections!")
                while True:
                        self.readList, self.writeList, [] = select.select(self.rList,self.wList,[],0)
                        for socket in self.readList:
                                #print(socket)
                                if socket is self.serversocket:
                                        #self.newConnection()
                                        clientSocket, address = self.serversocket.accept()
                                        self.rList.append(clientSocket)
                                        self.wList.append(clientSocket)
                                        self.socketList.append(clientSocket)
                                        print(str(address[0]) + " connected")
                                        #self.clientList.append(address[0])
                                        #print(address)
                                        # Dict = Key:Value, key must be a string!
                                        self.clientList.append({str(address):json.loads(clientSocket.recv(1024).decode('utf-8'))}) # NICKNAME , {('host', port):Nickname}

                                        clientSocket.send((json.dumps(self.clientList)+"\n").encode('utf-8')) # SEND ALL NICKNAMES IN THE ROOM

                                        self.updateUserlist(clientSocket)
                                        print("Connection! " + str(address)+"\n")
                                        print(self.clientList)
                                else:
                                        try:
                                                data = socket.recv(1024) # Need to check if any ERROR Messages have been sent! -> Add Message Type?
                                                if data:
                                                        ## Check if a user have left.
                                                        print("Check how the data is sent!")
                                                        print(data)


                                                        connectionClosedMessage = re.search('\n(.*?)\n',data.decode('utf-8')) # separates by \n and \n, is nothing is found -> return NONE
                                                        if connectionClosedMessage:
                                                                print("User left the channel!")
                                                                for Dict in self.clientList:
                                                                        #print(Dict)
                                                                        if Dict[json.loads(connectionClosedMessage.group(1))]:
                                                                                self.clientList.remove(Dict)
                                                                #print(self.clientList)
                                                                #print(self.socketList)

                                                        else:
                                                                self.sendMsg(data, socket)
                                                        

                                        except BrokenPipeError:
                                                print("Couldnt send, the connection was closed!")
                                                self.rList.remove(socket)
                                                self.wList.remove(socket)
                                                self.socketList.remove(socket)
                                                self.updateUserlist(socket)

                                        except ConnectionResetError: # Must remove the socket from clientList!
                                                print("data = socket.recv(1024) fail...")
                                                print("Connection Closed! ") #+ str(socket.getpeername()[0]))
                                                if socket in self.socketList:
                                                        self.rList.remove(socket)
                                                        self.wList.remove(socket)
                                                        self.socketList.remove(socket)
                                                        self.updateUserlist(socket)

        def sendMsg(self, data, client): # Sends the message to all clients!
                for socket in self.socketList:
                        if socket is not client and socket is not self.serversocket:
                                try:
                                        socket.send(data)
                                
                                except ConnectionResetError: # Must remove the socket from clientList!
                                        print("sendMsg ConnectionResetError Connection Closed! ") #+ str(socket.getpeername()[0]))
                                        socket.close()
                                        if socket in self.socketList:
                                                self.socketList.remove(socket)
                                                self.updateUserlist(socket)

                                except BrokenPipeError:
                                        print("sendMsg BrokenPipeError")
                                        self.rList.remove(socket)
                                        self.wList.remove(socket)
                                        socket.close()                                                
                                        if socket in self.socketList:
                                                self.socketList.remove(socket)
                                                self.updateUserlist(socket)


        def updateUserlist(self, client): # Send the updated UserList to every socket, except the new client and server.
                for socket in self.socketList:
                        if socket is not client and socket is not self.serversocket:
                                try:
                                        socket.send((json.dumps(self.clientList)+"\n").encode('utf-8')) # ex: b'["Derp"]'
                                
                                except ConnectionResetError:
                                        print("ConnectionResetError Connection Closed! ") #+ str(socket.getpeername()[0]))
                                        socket.close()
                                        if socket in self.socketList: # The socket is dead, remove it
                                                #print(self.socketList)
                                                self.socketList.remove(socket)
                                                self.updateUserlist(socket) # Update the UserList

                                except BrokenPipeError:
                                        print("updateUserlist BrokenPipeError")
                                        print(self.socketList)
                                        self.rList.remove(socket)
                                        self.wList.remove(socket)
                                        socket.close()
                                        if socket in self.socketList:
                                                self.socketList.remove(socket)
                                                self.updateUserlist(socket)

                                                
s = Server()

# Vid FEL i select.select: file descriptor cannot be a negative integer (-1) -> anslutningen till den Socket är closed, så vi försöker read/write on it.
# Kolla in Events
# dumps -> object      into Json string
# loads -> Json string into object

