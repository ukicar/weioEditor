import socket
import sys
import pickle

class UnixSocketClient:

    def __init__(self, name):
       
        # Create a UDS socket
        global sock
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        # define non-blocking socket
        sock.setblocking(0)
        # Connect the socket to the file where the server is listening
        server_address = "uds_" + name
        print >>sys.stderr, 'connecting to %s' % server_address
        try:
            sock.connect(server_address)
            
        except socket.error, msg:
            print >>sys.stderr, msg
            #I can't connect to the server, something is wrong I'll exit
            sys.exit(1)
    
    def send(self, messageObj):
        global sock
        try:
            
            # serialize object and prepare for transfer
            out = pickle.dumps(messageObj, pickle.HIGHEST_PROTOCOL)
            
            # print >>sys.stderr, 'sending "%s"' % message
            
            # Send data
            sock.sendall(out + "\n")
            
        except socket.error, msg:
            print >>sys.stderr, msg
            sys.exit(1)
    
    def close(self):
        print "closing connection"
        global sock
        # Strange thing, if I don't send something before closing Tornado will cut off
        # last information :|
        sock.sendAll("\n")
        sock.close()
    
    # TODO this part of code is not yet finished, receive will call handler in his parent
    def receive(self):
        try :
            data = sock.recv(1024)
            return data
        except :
            return None 