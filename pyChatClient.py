import socket
import json
import select
import queue
import threading
import re
import tkinter as tk

#class TopWinow(tk.Frame):
#
#
#    def __init__(self, parent):
#        tk.Frame.__init__(self, parent)
#        self.parent = parent



class GUI(tk.Frame):
    

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent

        # Main text box
        self.textbox = tk.Entry(self.parent.parent, bd=5)
        self.textarea = tk.Text(self.parent.parent, width=30, height=20)
 
        self.scrollbar = tk.Scrollbar(self.parent.parent)
        self.textarea.config(yscrollcommand=self.scrollbar.set, state=tk.DISABLED)
        self.scrollbar.config(command=self.textarea.yview)

        self.pad_x=5
        self.pad_y=5

        # User list
        self.users = tk.Text(self.parent.parent, width=17, height=10)
        self.users.config(state=tk.DISABLED)

        # Menu
        self.menubar = tk.Menu(self.parent.parent)
        self.serverpulldownmenu = tk.Menu(self.menubar, tearoff=0) # tearoff: dashed line ------
        self.serverpulldownmenu.add_command(label="Connect", command=self.newconnectwindow)
        self.serverpulldownmenu.add_command(label="Disconnect", command=self.parent.disconnectButtonChat)
        self.menubar.add_cascade(label="Server", menu=self.serverpulldownmenu)
        self.serverpulldownmenu.entryconfig("Disconnect", state="disabled")
        self.parent.parent.config(menu=self.menubar)

        # Messages
        self.textarea.grid(row=0, column=1, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)
        self.scrollbar.grid(row=0, column=2, padx=self.pad_x, pady=self.pad_y, sticky='ns')
        self.textbox.grid(row=1, column=1, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)
        # Users
        self.users.grid(row=0,column=4,padx=self.pad_x, pady=self.pad_y, sticky=tk.W)

        self.parent.parent.bind('<Return>', lambda x: self.parent.addChat())
        self.parent.parent.bind("<Escape>", lambda x: self.parent.exitChat())
        self.parent.parent.protocol('WM_DELETE_WINDOW', self.parent.exitChat)
        self.parent.parent.wm_title("pyChat")
        img = tk.PhotoImage(file='test2_icon.png') # .Gif, PPM/PGM, .PNG
        self.parent.parent.call('wm', 'iconphoto', self.parent.parent._w, img)

    def newconnectwindow(self): # New class?

        self.connecttop = tk.Toplevel()
        self.connecttop.title("Connect")

        self.connectbutton = tk.Button(self.connecttop, text="Connect", command=self.parent.threadStart)

        # Nickname
        self.textboxNickname = tk.Entry(self.connecttop, bd=5)
        self.buttonNick = tk.Button(self.connecttop, text="Set Nickname", command=self.parent.setNick)
        # Address
        self.textboxAddress = tk.Entry(self.connecttop, bd=5)
        self.buttonAddress = tk.Button(self.connecttop, text="Set Address", command=self.parent.setAddress)
        # Port
        self.textboxPort = tk.Entry(self.connecttop, bd=5)
        self.buttonPort = tk.Button(self.connecttop, text="Set Port", command=self.parent.setPort)

        # Nickname
        self.buttonNick.grid(row=0, column=4, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)
        self.textboxNickname.grid(row=0, column=3, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)
        # Address
        self.buttonAddress.grid(row=1, column=4, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)
        self.textboxAddress.grid(row=1, column=3, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)
        # Port
        self.buttonPort.grid(row=2, column=4, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)
        self.textboxPort.grid(row=2, column=3, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)

        self.connectbutton.grid(row=3, column=4, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)
        self.connecttop.resizable(0,0)

class Main(tk.Frame):


    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.gui = GUI(self)

        self.msgOutQ = queue.Queue()
        self.msgInQ = queue.Queue()
        self.userList = []

        self.nickname = None
        self.host = None
        self.port = None

        # Tells us if we are connected to the server and if we must close the connection or not!
        self.gotConnection = 0 
        # Tells us if we have created the client thread (see start())
        self.threadActive = 0 
        # Since start() can only be used ONCE!
        self.disconnectedflag = 0
        
        self.readList, self.writeList, self.rList, self.wList = [], [], [], []
        self.clientsocket = socket.socket()
        #self.clientsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.rList.append(self.clientsocket)
        self.wList.append(self.clientsocket)

        # Used since we cannot create the same thread multiple times.
        self.Event = threading.Event() 
        self.shutdownEvent = threading.Event()
        self.shutdownEvent.set()

        self.inputThread = threading.Thread(target = self.start, args=(self.Event, self.shutdownEvent,))                 
        self.parent.after(100, self.updateChat) # calls updateChat after 100ms

    def testPrint(self):
        print("Derp!")

    def threadStart(self):
        """ Starts the communication """
        if self.host and self.port and self.nickname:
            if not self.threadActive:
                self.inputThread.start() # start() can only be used ONCE!
                self.threadActive = 1
                self.gui.connecttop.destroy()
            else:
                print("self.Event.set()")
                self.Event.set()
                self.gui.connecttop.destroy()
        else:
            print("Please fill in all credentials!")

    def disconnectButtonChat(self):
        if self.gotConnection:

            host = self.clientsocket.getsockname() # A List
            tuplehost = str(tuple(host))

            self.clientsocket.send(("\n" + json.dumps(tuplehost)+"\n").encode('utf-8'))
            self.disconnectedflag = 1
            self.gotConnection = 0

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
            self.threadActive = 1

            #self.gui.connectbutton.config(text="Connect", command=self.threadStart)

            self.gui.textarea.config(state=tk.NORMAL)
            self.gui.textarea.delete('1.0', tk.END)
            self.gui.textarea.config(state=tk.DISABLED)

            self.gui.users.config(state=tk.NORMAL)
            self.gui.users.delete('1.0', tk.END)
            self.gui.users.config(state=tk.DISABLED)

            #self.gui.buttonAddress.config(state=tk.NORMAL)
            #self.gui.textboxAddress.config(state=tk.NORMAL)

            #self.gui.buttonPort.config(state=tk.NORMAL)
            #self.gui.textboxPort.config(state=tk.NORMAL)
            self.gui.serverpulldownmenu.entryconfig("Connect", state="normal") # Connect
            self.gui.serverpulldownmenu.entryconfig("Disconnect", state="disabled") # Disconnect

    def exitChat(self):
        """ Send a shutdown message to the server so it can remove it from the clientList """

        if self.gotConnection:
            host = self.clientsocket.getsockname() # A List
            tuplehost = str(tuple(host))

            self.clientsocket.send(("\n" + json.dumps(tuplehost) + "\n").encode('utf-8'))
            self.threadActive = 0 # Otherwise we get ValueError: select.select: file descriptor cannot be a negative integer (-1), as select.select is trying to read a socket that is closed.
            self.clientsocket.shutdown(socket.SHUT_RDWR)
            self.clientsocket.close()
            self.shutdownEvent.clear()
            self.parent.destroy()

        else:
            print("exitChat")
            self.shutdownEvent.clear()
            self.parent.destroy()

    def updateChat(self):
        """ Updates the chat room """

        if not self.msgInQ.empty():
            message = self.msgInQ.get()
            self.gui.textarea.config(state=tk.NORMAL)
            self.gui.textarea.insert(tk.END, message['nick'] + ": " + message['data'] + "\n") ##json.loads(self.msgInQ.get().decode('utf-8'))['data'] + "\n") #
            self.gui.textarea.see(tk.END)
            self.gui.textarea.config(state=tk.DISABLED)
        self.parent.after(100, self.updateChat)

    def addChat(self):
        """ Adds text that the client is writing to the chat room. """

        if self.gotConnection:
            text = self.gui.textbox.get()
            self.gui.textarea.config(state=tk.NORMAL)
            self.gui.textarea.insert(tk.END, self.nickname + ": "+text+"\n")
            self.gui.textarea.config(state=tk.DISABLED)
            self.gui.textarea.see(tk.END)
            msg = json.dumps({'addr': self.host, 'port': self.port, 'data': text, 'nick': self.nickname })+"\n"
            self.msgOutQ.put(msg)
            self.gui.textbox.delete(0, tk.END)

    def setNick(self):
        text = self.gui.textboxNickname.get()
        if text:
            self.nickname = text
            self.gui.buttonNick.config(state=tk.DISABLED)
            self.gui.textboxNickname.config(state=tk.DISABLED)
        else:
            print("Please enter a nickname!")

    def setAddress(self):
        adr = self.gui.textboxAddress.get()
        if not adr:
            print("Please enter an address!")
        else:
            self.host = adr
            self.gui.buttonAddress.config(state=tk.DISABLED)
            self.gui.textboxAddress.config(state=tk.DISABLED)

    def setPort(self):
        port = self.gui.textboxPort.get()
        if not port:
            print("Please enter a port!")
        else:
            self.port = int(port)
            self.gui.buttonPort.config(state=tk.DISABLED)
            self.gui.textboxPort.config(state=tk.DISABLED)

    def showConnectedUsers(self):
        self.gui.users.config(state=tk.NORMAL)
        self.gui.users.delete('0.0', tk.END)
        for i in range(len(self.userList)): # ('host', port):Nickname
            self.gui.users.insert(tk.END,list(self.userList[i].values())[0]+"\n")
        self.gui.users.config(state=tk.DISABLED)

    # Separate Thread!
    def start(self, ev, shutdownEvent):
        """ Handles communication """

        print("Connecting!")
        connection = None
        while shutdownEvent.is_set():
            while connection is None:
                try:
                    self.gui.textarea.config(state=tk.NORMAL)
                    self.gui.textarea.insert(tk.END, "Connecting!\n")
                    self.gui.textarea.see(tk.END)
                    self.gui.textarea.config(state=tk.DISABLED)
                    self.clientsocket.connect((self.host, self.port))
                    #print(self.clientsocket.getsockname())
                    self.gotConnection = 1
                    self.threadActive = 1
                    self.clientsocket.send((json.dumps(self.nickname)+"\n").encode('utf-8')) # Send Nickname
                    self.userList = json.loads(self.clientsocket.recv(1024).decode('utf-8')) # Gets the current chat rooms users
                    self.showConnectedUsers()
                    connection = 1
                    #self.gui.connectbutton.config(state=tk.NORMAL)
                    #self.gui.connectbutton.config(text="Disconnect", command= self.disconnectButtonChat)
                    self.gui.serverpulldownmenu.entryconfig("Connect", state="disabled")
                    self.gui.serverpulldownmenu.entryconfig("Disconnect", state="normal")
                    self.gui.textarea.insert(tk.END, "Connected!\n")
                except ConnectionRefusedError:
                    self.gui.textarea.config(state=tk.NORMAL)
                    self.gui.textarea.insert(tk.END, "Connection could not be made!\n")
                    self.gui.textarea.see(tk.END)
                    self.gui.textarea.config(state=tk.DISABLED)
                    #self.gui.connectbutton.config(state=tk.NORMAL)
                    #self.gui.connectbutton.config(text="Connect")
                    self.gui.serverpulldownmenu.entryconfig("Disconnect", state="disabled")
                    self.gui.serverpulldownmenu.entryconfig("Connect", state="normal")
                    connection = None
                    ev.wait() # Waits until Event.set() is called (makes the flag True)
                    ev.clear() # (makes the flag False´, Events are per default falsey)

            while self.gotConnection:
                if self.gotConnection:
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

            if self.disconnectedflag:
                self.gotConnection = 0
                connection = None
                ev.wait() # When the disconnect button is pressed, the thread waits here.
                ev.clear()
        return



if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(0,0)
    root.minsize(400, 200)
    Main(root)
    root.mainloop()

# ValueError: select.select: file descriptor cannot be a negative integer (-1), as select.select is trying to read a socket that is closed.
# Change the file extension to ".pyw" --- this removes the command prompt in the background.
# dumps -> object into Json string
# loads -> Json string into object




















