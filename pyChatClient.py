import socket
import json
import select
#import time
import queue
import threading
import re
#from tkinter import *
import tkinter as tk
#from tkinter import PhotoImage

class GUI():
    pass

#class Client():
#class Main(tk.Tk):


    def __init__(self):
        tk.Tk.__init__(self)
        self.msgOutQ = queue.Queue()
        self.msgInQ = queue.Queue()
        self.userList = []
        self.nickname = "Derp"

        # Tells us if we are connected to the server and if we must close the connection or not!
        self.connectionflag = 0 
        
        # Tells us if we have created the client thread (see start())
        self.clientActive = 0 
        
        self.disconnectButton = 0
        
        self.readList, self.writeList, self.rList, self.wList = [], [], [], []
        self.clientsocket = socket.socket()
        #self.clientsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host = '127.0.0.0' # Server ip
        self.port = 22 # Server port
        self.rList.append(self.clientsocket)
        self.wList.append(self.clientsocket)

        # Used since we cannot create the same thread multiple times.
        self.Event = threading.Event() 
        self.shutdownEvent = threading.Event()
        self.shutdownEvent.set()

        self.inputThread = threading.Thread(target = self.start, args=(self.Event, self.shutdownEvent,))       
        

        ###########################################################################

        self.root = Tk()
        self.root.resizable(0,0)
        self.root.minsize(400, 200)
        self.frame = Frame(self.root)

        self.button = Button(self.root, text="Connect", command=self.threadStart)
        self.L1 = Label(self.root, text="Message")
        
        # Main text box
        self.textbox = Entry(self.root, bd=5)
        self.textarea = Text(self.root, width=30, height=20)

        # Nickname
        self.textboxNickname = Entry(self.root, bd=5)
        self.buttonNick = Button(self.root, text="Set Nickname", command=self.setNick)

        # Address
        self.textboxAddress = Entry(self.root, bd=5)
        self.buttonAddress = Button(self.root, text="Set Address", command=self.setAddress)

        # Port
        self.textboxPort = Entry(self.root, bd=5)
        self.buttonPort = Button(self.root, text="Set Port", command=self.setPort)

        
        self.scrollbar = Scrollbar(self.root)
        self.textarea.config(yscrollcommand=self.scrollbar.set, state=DISABLED)
        self.scrollbar.config(command=self.textarea.yview)

        self.pad_x=5
        self.pad_y=5

        self.users = Text(self.root, width=17, height=10)
        self.users.config(state=DISABLED)

        # Messages
        self.textarea.grid(row=0, column=1, padx=self.pad_x, pady=self.pad_y, sticky=W)
        self.scrollbar.grid(row=0, column=2, padx=self.pad_x, pady=self.pad_y, sticky='ns')
        self.textbox.grid(row=1, column=1, padx=self.pad_x, pady=self.pad_y, sticky=W)

        # Connecting
        self.button.grid(row=1, column=2, padx=self.pad_x, pady=self.pad_y, sticky=W)

        # Users
        self.users.grid(row=0,column=4,padx=self.pad_x, pady=self.pad_y, sticky=W)

        #Nickname
        self.buttonNick.grid(row=1, column=4, padx=self.pad_x, pady=self.pad_y, sticky=W)
        self.textboxNickname.grid(row=1, column=3, padx=self.pad_x, pady=self.pad_y, sticky=W)

        #Address
        self.buttonAddress.grid(row=2, column=4, padx=self.pad_x, pady=self.pad_y, sticky=W)
        self.textboxAddress.grid(row=2, column=3, padx=self.pad_x, pady=self.pad_y, sticky=W)

        #Port
        self.buttonPort.grid(row=3, column=4, padx=self.pad_x, pady=self.pad_y, sticky=W)
        self.textboxPort.grid(row=3, column=3, padx=self.pad_x, pady=self.pad_y, sticky=W)

        self.root.bind("<Return>", lambda x: self.addChat())
        self.root.protocol('WM_DELETE_WINDOW', self.exitChat)
        self.root.wm_title("pyChat")

        img = PhotoImage(file='test2_icon.png') # .Gif, PPM/PGM, .PNG
        self.root.call('wm', 'iconphoto', self.root._w, img)

        ###########################################################################
          
        self.root.after(100, self.updateChat) # calls updateChat after 100ms
        self.root.mainloop()

    def threadStart(self):
        """ Starts the communication """

        if not self.clientActive:
            self.inputThread.start() # start() can only be used ONCE!
            self.clientActive = 1
        else:
            print("self.Event.set()")
            self.Event.set()

    def disconnectButtonChat(self):
        if self.connectionflag:

            host = self.clientsocket.getsockname() # A List
            tuplehost = str(tuple(host))

            self.clientsocket.send(("\n" + json.dumps(tuplehost)+"\n").encode('utf-8'))
            self.disconnectButton = 1
            self.connectionflag = 0

            self.clientsocket.shutdown(socket.SHUT_RDWR)

            # all future operations on the socket object will fail because socket.close()
            self.clientsocket.close() 

            # Remove the old socket object
            self.rList.remove(self.clientsocket) 
            self.wList.remove(self.clientsocket)

            # Must create a new socket object
            self.clientsocket = socket.socket() 

            # Insert the new socket object
            self.rList.append(self.clientsocket)
            self.wList.append(self.clientsocket)

            # Otherwise when we press Connect again, it tries to start a new thread, which we cannot do.
            self.clientActive = 1

            self.button.config(text="Connect", command=self.threadStart)

            self.textarea.config(state=NORMAL)
            self.textarea.delete('1.0', END)
            self.textarea.config(state=DISABLED)

            self.users.config(state=NORMAL)
            self.users.delete('1.0', END)
            self.users.config(state=DISABLED)

            self.buttonAddress.config(state=NORMAL)
            self.textboxAddress.config(state=NORMAL)

            self.buttonPort.config(state=NORMAL)
            self.textboxPort.config(state=NORMAL)

    def exitChat(self):
        """ Send a shutdown message to the server so it can remove it from the clientList """

        if self.connectionflag:
            host = self.clientsocket.getsockname() # A List
            tuplehost = str(tuple(host))

            self.clientsocket.send(("\n" + json.dumps(tuplehost) + "\n").encode('utf-8'))
            self.clientActive = 0 # Otherwise we get ValueError: select.select: file descriptor cannot be a negative integer (-1), as select.select is trying to read a socket that is closed.
            self.clientsocket.shutdown(socket.SHUT_RDWR)
            self.clientsocket.close()
            self.shutdownEvent.clear()
            self.root.destroy()

        else:
            print("exitChat")
            self.shutdownEvent.clear()
            self.root.destroy()

    def updateChat(self):
        """ Updates the chat room """

        if not self.msgInQ.empty():
            message = self.msgInQ.get()
            self.textarea.config(state=NORMAL)
            self.textarea.insert(END, message['nick'] + ": " + message['data'] + "\n") ##json.loads(self.msgInQ.get().decode('utf-8'))['data'] + "\n") #
            self.textarea.see(END)
            self.textarea.config(state=DISABLED)
        self.root.after(100, self.updateChat)

    def addChat(self):
        """ Adds text that the client is writing to the chat room. """

        if self.connectionflag:
            text = self.textbox.get()
            self.textarea.config(state=NORMAL)
            self.textarea.insert(END, self.nickname + ": "+text+"\n")
            self.textarea.config(state=DISABLED)
            self.textarea.see(END)
            msg = json.dumps({'addr': self.host, 'port': self.port, 'data': text, 'nick': self.nickname })+"\n"
            self.msgOutQ.put(msg)
            self.textbox.delete(0, END)

    def setNick(self):
        text = self.textboxNickname.get()
        if text:
            self.nickname = text
            self.buttonNick.config(state=DISABLED)
            self.textboxNickname.config(state=DISABLED)
        else:
            print("Please enter a nickname")

    def setAddress(self):
        adr = self.textboxAddress.get()
        self.host = adr
        self.buttonAddress.config(state=DISABLED)
        self.textboxAddress.config(state=DISABLED)

    def setPort(self):
        port = self.textboxPort.get()
        self.port = int(port)
        self.buttonPort.config(state=DISABLED)
        self.textboxPort.config(state=DISABLED)

    def showConnectedUsers(self):
        self.users.config(state=NORMAL)
        self.users.delete('0.0', END)
        for i in range(len(self.userList)): # ('host', port):Nickname
            self.users.insert(END,list(self.userList[i].values())[0]+"\n")
        self.users.config(state=DISABLED)

    # Separate Thread!
    def start(self, ev, shutdownEvent):
        """ Handles communication """

        print("Connecting!")
        connection = None
        while shutdownEvent.is_set():
            while connection is None:
                try:
                    self.textarea.config(state=NORMAL)
                    self.textarea.insert(END, "Connecting!\n")
                    self.textarea.see(END)
                    self.textarea.config(state=DISABLED)
                    self.clientsocket.connect((self.host, self.port))
                    #print(self.clientsocket.getsockname())
                    self.connectionflag = 1
                    self.clientActive = 1
                    self.clientsocket.send((json.dumps(self.nickname)+"\n").encode('utf-8')) # Send Nickname
                    self.userList = json.loads(self.clientsocket.recv(1024).decode('utf-8')) # Gets the current chat rooms users
                    self.showConnectedUsers()
                    connection = 1
                    self.button.config(state=NORMAL)
                    self.button.config(text="Disconnect", command= self.disconnectButtonChat)
                except ConnectionRefusedError:
                    self.textarea.config(state=NORMAL)
                    self.textarea.insert(END, "Connection could not be made!\n")
                    self.textarea.see(END)
                    self.textarea.config(state=DISABLED)
                    self.button.config(state=NORMAL)
                    self.button.config(text="Connect")
                    connection = None
                    ev.wait() # Waits until Event.set() is called (makes the flag True)
                    ev.clear() # (makes the flag False´, Events are per default falsey)

            while self.connectionflag:
                if self.connectionflag:
                    self.readList, self.writeList, [] = select.select(self.rList, self.wList, [], 0) # select.select(rList, wList, [], timeout=0 -> Never blocks!)

                    while not self.msgOutQ.empty():
                        message = self.msgOutQ.get()
                        for socket in self.writeList: # Send to all the users
                            socket.send(message.encode('utf-8'))

                    for socket in self.readList:
                        try:
                            data = socket.recv(1024)
                            if data: # Check the data type! List -> Userlist

                                #print(json.loads(data.decode('utf-8'))['data'])
                                #print("Data")
                                #print(data) # Must Separate the messages!
                                #print(data.decode('utf-8')) # ["Derp", "Derp"]{"data": "j", "port": 9000, "addr": "127.0.0.0"}{"data": "j", "port": 9000, "addr": "127.0.0.0"}
                                #print(type(data.decode('utf-8'))) # str

                                listOfData = re.findall('(.*?)\n', data.decode('utf-8')) # separates by \n
                                print("ListOfData")
                                print(listOfData)
                                #checktype = json.loads(data.decode('utf-8'))
                                for d in listOfData:
                                    msg = json.loads(d)
                                    if type(msg) is list:
                                        self.userList = msg #NICKNAMES
                                        self.showConnectedUsers()
                                    else:    
                                        self.msgInQ.put(msg)
                        except:
                            print("Error!")

            if self.disconnectButton:
                self.connectionflag = 0
                connection = None
                ev.wait() # When the disconnect button is pressed, the thread waits here.
                ev.clear()
        return


if __name__ == "__main__":
    #c = Client()
    #root = tk.tk()
    #Main(root)
    app = Main()
    app.mainloop()

# ValueError: select.select: file descriptor cannot be a negative integer (-1), as select.select is trying to read a socket that is closed.
# Change the file extension to ".pyw" --- this removes the command prompt in the background.
# dumps -> object into Json string
# loads -> Json string into object




















