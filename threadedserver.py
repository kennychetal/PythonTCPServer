
import random
import string
import threading
import sqlite3
import os

from PyQt4 import QtCore
from PyQt4.QtNetwork import QTcpServer
from PyQt4.QtNetwork import QTcpSocket
from PyQt4.QtNetwork import QHostAddress
from PyQt4.QtCore import QObject

class Server(QTcpServer):
    def __init__(self, parent = None):
        super(QTcpServer, self).__init__(parent)
        
        # Starts listening on selected port.
        port = 32000
        started = self.listen(address = QHostAddress.Any, port = port)
        
        # It is possible that such port is not available.
        if started:
            print 'Listening on port %s' % port
            
        else:
            print 'Could not bind port %s' % port
        
        # This dictionary will always contains a reference to all 
        #current sockets.
        self.sockets = {}
            
    # This method is automatically called by Qt when 
    # a peer has connected.
    def incomingConnection(self, socket_descriptor):
        
        print 'New connection...'
        
        # Constructs a Socket object with the socket_descriptor
        # passed by Qt.
        newsocket = Socket(self)
        newsocket.setSocketDescriptor(socket_descriptor)
        
        # When the Socket has been read, call the 'readSocket' function.
        self.connect(newsocket, QtCore.SIGNAL('readyReadId'), self.readSocket)
	self.connect(newsocket, QtCore.SIGNAL('closedId'), self.closeSocket)        

        # Generates a random string in order to tell sockets apart, and make sure it's unique.
        rand_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(3))
        
        while rand_id in self.sockets.keys():
            rand_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(3))
        
        # Keeps a reference to this socket on the 'sockets' dictionary, the random string is the key.
        # Also set the key to the Socket object.
        self.sockets[rand_id] = newsocket
        newsocket.setId(rand_id)
        
    def readSocket(self, socket_id):
    
        try:
            # Takes the socket from the dictionary, using the socket_id, then read the data.
            readysocket = self.sockets.get(socket_id)
            socket_info = readysocket.readAll()
            
            print 'Socket Info: %s' % socket_info.data()
            
            # Create a thread for handling the data, emit 'ready' when done inside run(), 
            # so 'socketReady' gets called.
            socket_thread = ThreadAction(socket_info, socket_id)
            self.connect(socket_thread.paramSender, QtCore.SIGNAL('ready'), self.socketReady)
            
            # Do something with the data.
            socket_thread.start()
            
        except KeyError:
            print 'Error, socket not in queue.'

    def closeSocket(self, socket_id):

	try:
	    closedsocket = self.sockets.pop(socket_id)
             
	    print 'Socket closed: %s' % socket_id

	except KeyError:
 	    print 'Error, socket not in queue.'
            
    def socketReady(self, socket_id, text):
        try:            
            # The following lines are for clean up purposes. Uncomment only
            # if you want to close the socket.
            '''
            in_socket = self.sockets.pop(socket_id)
            self.connect(in_socket, QtCore.SIGNAL('bytesWritten()'), in_socket, QtCore.SLOT('deleteLater()'))
            '''
	            
            # Uncomment the following line if you want to write something back 
            # to the peer.
            #in_socket.write("Reply")
            
            print "Message: '%r' from socket %s has been processed." % (str(text), socket_id)
            
        except KeyError:
            print 'Error, socket not in queue.'
          
class Socket(QTcpSocket):
    def __init__(self, parent = None):
        super(QTcpSocket, self).__init__(parent)
        
        # The 'readyRead' signal is from QTcpSocket, call 'readyReadId' 
        # whenever is emitted.
        self.connect(self, QtCore.SIGNAL('readyRead()'), self.readyReadId)
	self.connect(self, QtCore.SIGNAL('disconnected()'), self.closedId)
    
    def setId(self, socket_id):
        self.id = socket_id
        
    def readyReadId(self):
        
        # Re-emits a ready signal that sends the ID, so the Server knows
        # which socket is ready.
        print 'Emitting signal!'
        self.emit(QtCore.SIGNAL('readyReadId'), (self.id))

    def closedId(self):
	
	# Re-emits a ready signal that tells the server that the client
	# closed the socket.
	print 'Client closed'
	self.emit(QtCore.SIGNAL('closedId'), (self.id))

lock = threading.Lock()

# Thread class based on Python's standard threading class.
class ThreadAction(threading.Thread):
    def __init__(self, socket_info, socket_id):
        threading.Thread.__init__(self)
        
        # Includes the unique id and the message.
        self.socket_id = socket_id
        self.socket_info = socket_info
        
        # QObject object for signaling purposes. 
        self.paramSender = Signaler()
    
    def run(self):
        lock.acquire()
        
        ##
        ## Do something with the socket_info (message) 
        ## and don't forget to signal 'ready'.
        ##
        
        # Passing the socket_id as first parameter is mandatory, 
        # second argument can be any string.
        self.paramSender.signalReady(self.socket_id, self.socket_info)
        lock.release()

class Signaler(QObject):
    def __init__(self, parent = None):
        super(QObject, self).__init__(parent)
     
    def signalReady(self, socket_id, text):
        self.emit(QtCore.SIGNAL('ready'), (socket_id), (text))
        
