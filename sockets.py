import select
import socket
from config import config
from module import Module

__author__ = 'm'


class ClientSocket(Module):
    def __init__(self, server1, connection, remote_addr, connector):
        super(ClientSocket, self).__init__(server1)
        self.__connected = True
        self.__socket = connection
        self.__remote_addr = remote_addr
        self.__buffer = b''
        self.__write_buffer = []
        self.__connector = connector(server1, self)

        self.__socket.setblocking(False)
        self._server.epoll.register(self.__socket, lambda events: self.__handle(events))

    def __handle(self, events):
        assert events
        if events & select.EPOLLIN:
            events &= ~ select.EPOLLIN
            while True:
                try:
                    data = self.__socket.recv(4096)
                except socket.error as why:
                    if why.args[0] in (socket.EAGAIN, socket.EWOULDBLOCK):
                        break
                    else:
                        raise why
                if data is None or not data:
                    self.disconnect()
                    break
                assert data
                self._log("received from socket#%d: %s" % (self.__socket.fileno(), ' '.join('%02x' % x for x in data)),
                          verbosity=3)

                data = data.split(b'\n')
                for chunk in data[:-1]:
                    yield lambda: self.execute(self.__buffer + chunk)
                    self.__buffer = b''
                self.__buffer = data[-1]

        if events & select.EPOLLOUT:
            while len(self.__write_buffer):
                try:
                    r = self.__socket.send(self.__write_buffer[0])
                except socket.error as why:
                    if why.args[0] in (socket.EAGAIN, socket.EWOULDBLOCK):
                        break
                    else:
                        raise why
                assert r > 0
                if r < len(self.__write_buffer[0])
                    self.__write_buffer[0] = self.__write_buffer[0][r:]
                    break
                self.__write_buffer = self.__write_buffer[1:]
            events &= ~ select.EPOLLOUT

        if events & select.EPOLLERR:
            self.disconnect()
            events &= ~ select.EPOLLERR

        if events & select.EPOLLHUP:
            self.disconnect()
            events &= ~ select.EPOLLHUP

        if events:
            self.__log("unhandled poll events: 0x%04x\n" % events)
        assert not events

    def disconnect(self):
        if not self.__connected:
            return
        self._log("connection #%d closed" % self.__socket.fileno())
        self._server.epoll.unregister(self.__socket)
        self.__socket.close()
        self.__write_buffer = []
        self.__connected = False

    def write(self, data):
        if len(data) == 0 or not self.__connected:
            return
        if self.__write_buffer:
            self.__write_buffer.append(data)
            return
        try:
            r = self.__socket.send(data)
        except socket.error as why:
            if why.args[0] in (socket.EAGAIN, socket.EWOULDBLOCK):
                r = 0
            else:
                raise why
        if r == len(data):
            return
        self.__write_buffer.append(data[r:])

    def execute(self, command):
        self._log("command from connection #%d: %s" % (self.__socket.fileno(), command.decode('iso8859-1')))
        self.__connector(command)


class ServerSocket(Module):
    def __init__(self, server1, connector):
        super(ServerSocket, self).__init__(server1)
        self.__connector = connector
        self.__socket = socket.socket(
            type=socket.SOCK_STREAM | socket.SOCK_NONBLOCK
        )
        self.__socket.bind((config["serve"], config['port']))
        self.__socket.listen(5)
        self._server.epoll.register(self.__socket, lambda events: self.__handle(events))

    def __handle(self, events):
        assert events
        if events & select.EPOLLIN:
            events &= ~ select.EPOLLIN
            while True:
                try:
                    client, remote_addr = self.__socket.accept()
                except socket.error as why:
                    if why.args[0] in (socket.EAGAIN, socket.EWOULDBLOCK):
                        break
                    else:
                        self._log("unknown socket error: " + str(why))
                        raise why
                except Exception as e:
                    self._log(e, "E")
                    break
                self._log("accepted client [%s]: %s" % (remote_addr, client))
                ClientSocket(self._server, client, remote_addr, self.__connector)
        assert not events

