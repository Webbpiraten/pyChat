import socket
import json
import select
import queue
import threading
import re
import tkinter as tk

#class ConWinow(tk.Frame):
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
        self.users = tk.Text(self.parent.parent, width=17, height=20)
        self.users.config(state=tk.DISABLED)

        # Menu
        self.menubar = tk.Menu(self.parent.parent)
        self.serverpulldownmenu = tk.Menu(self.menubar, tearoff=0) # tearoff: dashed line ------
        self.serverpulldownmenu.add_command(label="Connect", command=self.newconnectwindow)
        self.serverpulldownmenu.add_command(label="Disconnect", command=self.parent.disconnectChat)
        self.menubar.add_cascade(label="Server", menu=self.serverpulldownmenu)
        self.serverpulldownmenu.entryconfig("Disconnect", state="disabled")
        self.parent.parent.config(menu=self.menubar)

        # Messages
        self.textarea.grid(row=0, column=1, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)
        self.scrollbar.grid(row=0, column=2, padx=self.pad_x, pady=self.pad_y, sticky='ns')
        self.textbox.grid(row=1, column=1, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)
        # Users
        self.users.grid(row=0,column=4,padx=self.pad_x, pady=self.pad_y, sticky=tk.W)

        self.parent.parent.bind('<Return>', lambda x: self.parent.addToChat())
        self.parent.parent.bind("<Escape>", lambda x: self.parent.exitChat())
        self.parent.parent.protocol('WM_DELETE_WINDOW', self.parent.exitChat)
        self.parent.parent.wm_title("pyChat")
        img = tk.PhotoImage(file='test2_icon.png') # .Gif, PPM/PGM, .PNG
        self.parent.parent.call('wm', 'iconphoto', self.parent.parent._w, img)

    def writeToChat(self, text):

        self.textarea.config(state=tk.NORMAL)
        self.textarea.insert(tk.END, text + "\n")
        self.textarea.see(tk.END)
        self.textarea.config(state=tk.DISABLED)

    def newconnectwindow(self): # New class?

        self.connecttop = tk.Toplevel()
        self.connecttop.title("Connect")

        self.connectbutton = tk.Button(self.connecttop, text="Connect", command=self.parent.chatInit)

        self.nicklabel = tk.Label(self.connecttop, text="Nickname")
        self.addrlabel = tk.Label(self.connecttop, text="Address")
        self.portlabel = tk.Label(self.connecttop, text="Port")

        # Nickname
        self.textboxNickname = tk.Entry(self.connecttop, bd=5)
        #self.buttonNick = tk.Button(self.connecttop, text="Set Nickname", command=self.parent.setNick)
        # Address
        self.textboxAddress = tk.Entry(self.connecttop, bd=5)
        #self.buttonAddress = tk.Button(self.connecttop, text="Set Address", command=self.parent.setAddress)
        # Port
        self.textboxPort = tk.Entry(self.connecttop, bd=5)
        #self.buttonPort = tk.Button(self.connecttop, text="Set Port", command=self.parent.setPort)

        self.nicklabel.grid(row=0, column=0, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)
        self.addrlabel.grid(row=1, column=0, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)
        self.portlabel.grid(row=2, column=0, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)

        # Nickname
        #self.buttonNick.grid(row=0, column=4, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)
        self.textboxNickname.grid(row=0, column=3, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)
        # Address
        #self.buttonAddress.grid(row=1, column=4, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)
        self.textboxAddress.grid(row=1, column=3, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)
        # Port
        #self.buttonPort.grid(row=2, column=4, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)
        self.textboxPort.grid(row=2, column=3, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)

        self.connectbutton.grid(row=3, column=3, padx=self.pad_x, pady=self.pad_y, sticky=tk.W)
        self.connecttop.resizable(0,0)

class Main(tk.Frame):


    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.gui = GUI(self)

        self.msgOutQ = queue.Queue()
        self.msgInQ = queue.Queue()
        self.userList = [] # Remove?

        self.nickname = None
        self.host = None
        self.port = None

        # Tells us if we must close the connection
        self.gotConnection = 0 
        # Tells us if we have any threads active (see start())
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

    def testPrint(self): # Debug
        print("Derp!")

    def chatInit(self):
        self.setNick()
        self.setAddress()
        self.setPort()
        self.threadStart()

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

    def closeServerConnection(self): # wait for server confirmation
            host = self.clientsocket.getsockname() # A List
            tuplehost = str(tuple(host))
            self.clientsocket.send(("\n" + json.dumps(tuplehost)+"\n").encode('utf-8'))
            #response = self.clientsocket.recv(1024)
            #if response:
            #    return True
            #else:
            #    print("Server not responding...")

    def disconnectChat(self):
        """ Disconnecting but not closing the client, sends a shutdown message """

        if self.gotConnection:

            host = self.clientsocket.getsockname() # A List
            tuplehost = str(tuple(host))

            # Change, insert into MsgOutQ?
            # Wait for confirmation?
            self.clientsocket.send(("\n" + json.dumps(tuplehost)+"\n").encode('utf-8'))

            self.disconnectedflag = 1
            self.gotConnection = 0

            self.clientsocket.shutdown(socket.SHUT_RDWR)

            # all future operations on the socket object will fail because socket.close()
            self.clientsocket.close() # Releases resources

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

            self.gui.textarea.config(state=tk.NORMAL)
            self.gui.textarea.delete('1.0', tk.END)
            self.gui.textarea.config(state=tk.DISABLED)

            self.gui.users.config(state=tk.NORMAL)
            self.gui.users.delete('1.0', tk.END)
            self.gui.users.config(state=tk.DISABLED)

            self.gui.serverpulldownmenu.entryconfig("Connect", state="normal")
            self.gui.serverpulldownmenu.entryconfig("Disconnect", state="disabled")

    def exitChat(self):
        """ Closing the client, sends a shutdown message """

        if self.gotConnection:
            host = self.clientsocket.getsockname() # A List
            tuplehost = str(tuple(host))

            # Change, insert into MsgOutQ?
            # Wait for confirmation?
            self.clientsocket.send(("\n" + json.dumps(tuplehost) + "\n").encode('utf-8'))

            self.threadActive = 0 # Otherwise we get ValueError: select.select: file descriptor cannot be a negative integer (-1), as select.select is trying to read a socket that is closed.
            self.clientsocket.shutdown(socket.SHUT_RDWR)
            self.clientsocket.close()
            self.shutdownEvent.clear() # <- Not needed
            self.parent.destroy()
        else:
            #print("exitChat")
            self.shutdownEvent.clear() # <- Not needed
            self.parent.destroy()

    def updateChat(self):
        """ Updates the chat room """

        if not self.msgInQ.empty():
            message = self.msgInQ.get()
            self.gui.writeToChat(message['nick'] + ": " + message['data'])
            #self.gui.textarea.config(state=tk.NORMAL)
            #self.gui.textarea.insert(tk.END, message['nick'] + ": " + message['data'] + "\n") ##json.loads(self.msgInQ.get().decode('utf-8'))['data'] + "\n") #
            #self.gui.textarea.see(tk.END)
            #self.gui.textarea.config(state=tk.DISABLED)
        self.parent.after(100, self.updateChat)

    def addToChat(self):
        """ Adds text that the client is writing to the chat room. """

        if self.gotConnection:
            text = self.gui.textbox.get()
            self.gui.writeToChat(self.nickname + ": "+text)
            msg = json.dumps({'addr': self.host, 'port': self.port, 'data': text, 'nick': self.nickname })+"\n"
            self.msgOutQ.put(msg)
            self.gui.textbox.delete(0, tk.END)

    def setNick(self):
        text = self.gui.textboxNickname.get()
        if text:
            self.nickname = text
        else:
            print("Please enter a nickname!")

    def setAddress(self): # Save addresses?
        adr = self.gui.textboxAddress.get()
        if not adr:
            print("Please enter an address!")
        else:
            self.host = adr

    def setPort(self):
        port = self.gui.textboxPort.get()
        if not port:
            print("Please enter a port!")
        else:
            self.port = int(port)

    def showConnectedUsers(self):
        self.gui.users.config(state=tk.NORMAL)
        self.gui.users.delete('0.0', tk.END)
        for i in range(len(self.userList)): # ('host', port):Nickname
            self.gui.users.insert(tk.END,list(self.userList[i].values())[0]+"\n")
        self.gui.users.config(state=tk.DISABLED)

    # Message types? message, newConnection, shutdown, heartbeat ?
    # message:  {"msg":   0, "nick":nick, "adr": adr, "port":port, "data":data}
    # newCon:   {"newC":  0, "nick":nick, "adr": adr, "port":port}
    # shutdown: {"shutd": 0, "adr": adr,  "port":port}
    # heartb:   {"heartb":0, "adr": adr,  "port":port}
    def start(self, ev, shutdownEvent):
        """ Handles communication, separate Thread """

        print("Connecting!")
        connection = None
        while shutdownEvent.is_set():
            while connection is None:
                try:
                    self.gui.writeToChat("Connecting!")
                    self.clientsocket.connect((self.host, self.port))
                    self.gotConnection = 1
                    self.threadActive = 1
                    self.clientsocket.send((json.dumps(self.nickname)+"\n").encode('utf-8')) # Send Nickname
                    self.userList = json.loads(self.clientsocket.recv(1024).decode('utf-8')) # Gets the current chat rooms users
                    self.showConnectedUsers()
                    connection = 1
                    self.gui.serverpulldownmenu.entryconfig("Connect", state="disabled")
                    self.gui.serverpulldownmenu.entryconfig("Disconnect", state="normal")
                    self.gui.textarea.insert(tk.END, "Connected!\n")
                except ConnectionRefusedError:
                    self.gui.writeToChat("Connection could not be made!")
                    self.gui.serverpulldownmenu.entryconfig("Connect", state="normal")
                    self.gui.serverpulldownmenu.entryconfig("Disconnect", state="disabled")
                    connection = None
                    ev.wait() # Waits until Event.set() (makes the flag True)
                    ev.clear() # (makes the flag False, Events are per default falsey)

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
                            if data: # Check shutdown messages
                                # Check the data type! List -> Userlist

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
                self.host = None
                self.port = None
                ev.wait() # When disconnecting, the thread waits.
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




















