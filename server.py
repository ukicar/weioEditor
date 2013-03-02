# -*- coding: utf-8 -*-
import math
import subprocess
import os, signal
import socket
import pickle
import functools
import errno
import os
from tornado import web, ioloop, iostream

from sockjs.tornado import SockJSRouter, SockJSConnection

p = None

class PlayHandler(SockJSConnection):
    def on_open(self, info):
        pass
        
    def on_message(self, msg):
        global p
        
        #TODO check if something is already running
        # kill worker if is running
        #if p.poll() is not None :
         #   pass
            # try :
            #            self.timeout.stop()
            #            except :
            #                pass
            #            # TODO maybe use terminate here insted, this is barbarian??
            #            os.killpg(p.pid, signal.SIGTERM)
        
        #open weio_main.py file and write code inside
        
        processName = 'weio_main'
        
        f = open(processName +'.py', 'wb')
        f.write(msg)
        f.close()
        
        #launch process
        
        self.pipe = p = subprocess.Popen(['python', '-u', processName + '.py'],
        stdout=subprocess.PIPE)
        ioloop.IOLoop.instance().add_callback(self.on_subprocess_result)
        
        # UNIX DOMAIN SOCKET
        # Here we are launching Unix Socket Domain Socket Server, so we can communicate
        # with our process in two ways
        
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0)
        #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # 0 means non blocking socket
        sock.setblocking(0)
        # this has to be uds_nameOfProcess
        server_address = 'uds_' + processName

        # Make sure the socket does not already exist
        try:
            os.unlink(server_address)
        except OSError:
            if os.path.exists(server_address):
                raise
                

        sock.bind(server_address)
        # how many connections I can accept
        sock.listen(10)
        
        # add to io loop
        io_loop = ioloop.IOLoop.instance()
        callback = functools.partial(uds_socket_connection_ready, sock)
        io_loop.add_handler(sock.fileno(), callback, io_loop.READ)


    def on_subprocess_result(self):
      line = self.pipe.stdout.readline()
      
      if line :
          print line
          self.send(line)
          ioloop.IOLoop.instance().add_callback(self.on_subprocess_result)
        
        # p = subprocess.Popen(['python', '-u', "weio_main.py"], stdout=subprocess.PIPE)
        # self.timeout = ioloop.PeriodicCallback(self._weio_main, 50)
        # self.timeout.start()
        
        
        
    def _weio_main(self):
        print "prosao"

        if p.poll() is not None :
            self.timeout.stop()
            return

        print "usao u msg"
        line = p.stdout.readline()
        if line :
            self.send(line)

# UNIX DOMAIN SOCKET CALLBACK
def uds_socket_connection_ready(sock, fd, events):
    while True:
        try:
            connection, address = sock.accept()
            print "client connected to UNIX domain socket"
        except socket.error, e:
            if e[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
                raise
            return
        connection.setblocking(0)
        global stream
        stream = iostream.IOStream(connection)
        #stream.write("HTTP/1.0 200 OK\r\nContent-Length: 5\r\n\r\nPong!\r\n", stream.close)
        #stream.read_until("\n", on_receive)
        stream.read_until_close(on_close_socket, streaming_callback=on_receive)
        # Strange thing, if I don't send something thru socket before closing
        # Tornado will cut off last chunk of data :|
            
def on_receive(data):
    # Grabs data from socket and unpickle it
    recv = pickle.loads(data)
    print "from socket :", recv
    
def on_close_socket(data):
    # closing socket, communication is over
    # After that I'm listening for new connections
    global stream
    stream.close()
    print "stream is closed"

class WeioHandler(SockJSConnection):

    def on_open(self, info):
        #read default file and send it to browser
        inputFile = open('weio_main.py', 'r')
        script = inputFile.read()
        inputFile.close()
        
        self.send(script)



class EchoConnection(SockJSConnection):
    def on_message(self, msg):
        self.send(msg)


class CloseConnection(SockJSConnection):
    def on_open(self, info):
        self.close()

    def on_message(self, msg):
        pass


class TickerConnection(SockJSConnection):
    def on_open(self, info):
        self.timeout = ioloop.PeriodicCallback(self._ticker, 1000)
        self.timeout.start()

    def on_close(self):
        self.timeout.stop()

    def _ticker(self):
        self.send('tick!')


class BroadcastConnection(SockJSConnection):
    clients = set()

    def on_open(self, info):
        self.clients.add(self)

    def on_message(self, msg):
        self.broadcast(self.clients, msg)

    def on_close(self):
        self.clients.remove(self)


class AmplifyConnection(SockJSConnection):
    def on_message(self, msg):
        n = int(msg)
        if n < 0 or n > 19:
            n = 1

        self.send('x' * int(math.pow(2, n)))


class CookieEcho(SockJSConnection):
    def on_message(self, msg):
        self.send(msg)


if __name__ == '__main__':
    import logging
    logging.getLogger().setLevel(logging.DEBUG)
    
    WeioPlayRouter = SockJSRouter(PlayHandler, '/play')
    WeioRouter = SockJSRouter(WeioHandler, '/weio')
    EchoRouter = SockJSRouter(EchoConnection, '/echo',
                            user_settings=dict(response_limit=4096))
    WSOffRouter = SockJSRouter(EchoConnection, '/disabled_websocket_echo',
                            user_settings=dict(disabled_transports=['websocket']))
    CloseRouter = SockJSRouter(CloseConnection, '/close')
    TickerRouter = SockJSRouter(TickerConnection, '/ticker')
    AmplifyRouter = SockJSRouter(AmplifyConnection, '/amplify')
    BroadcastRouter = SockJSRouter(BroadcastConnection, '/broadcast')
    CookieRouter = SockJSRouter(CookieEcho, '/cookie_needed_echo')

    app = web.Application(WeioPlayRouter.urls +
                          WeioRouter.urls +
                          EchoRouter.urls +
                          WSOffRouter.urls +
                          CloseRouter.urls +
                          TickerRouter.urls +
                          AmplifyRouter.urls +
                          BroadcastRouter.urls +
                          CookieRouter.urls
                          )

    app.listen(8081)
    logging.info(" [*] Listening on 0.0.0.0:8081")
    ioloop.IOLoop.instance().start()
