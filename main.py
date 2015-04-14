#!/usr/bin/env python3

__author__ = 'burunduk3'

import itertools
import select
import signal
import socket

from logger import Logger
from config import config


class Server:
    def __init__(self, logger):
        self.__log = logger
        self.__finish = False
        signal.signal(signal.SIGTERM, lambda signo, frame: self.__signal(signo))
        signal.signal(signal.SIGUSR1, lambda signo, frame: self.__signal(signo))
        # TODO: mode signals (HUP)

    def __signal(self, signo):
        if signo == signal.SIGTERM:
            self.__log("[SIGTERM]")
            self.__finish = True
        elif signo == signal.SIGUSR1:
            self.__log.reopen()
            self.__log("logs rotated")

    def run(self, start_actions):
        actions = []
        try:
            while True:
                actions = list(actions)
                if not actions:
                    if self.__finish:
                        break
                    actions = start_actions
                logger("actions: %s" % actions, verbosity=5)
                continuations = [action() for action in actions]
                actions = itertools.chain(*filter(lambda x: x is not None, continuations))
        except KeyboardInterrupt:
            self.__log("[Ctrl+C]")
        self.__log("TODO: graceful exit (close all sockets etc)")

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGUSR1, signal.SIG_DFL)
        self.__log("TODO: close all sockets")


class Epoll:
    def __init__(self, logger):
        self.__log = logger
        self.__epoll = select.epoll(flags=select.EPOLL_CLOEXEC)
        self.__callback = {}

    def register(self, handler, callback):
        fileno = handler.fileno()
        assert fileno not in self.__callback
        self.__callback[fileno] = callback
        self.__epoll.register(handler,
                              select.EPOLLIN | select.EPOLLOUT | select.EPOLLERR | select.EPOLLHUP | select.EPOLLET)

    def unregister(self, handler):
        fileno = handler.fileno()
        self.__epoll.unregister(handler)
        del self.__callback[fileno]

    def poll(self, timeout=-1, default_action=None):
        self.__log("poll from epoll#%d" % self.__epoll.fileno(), verbosity=4)
        try:
            for fileno, events in self.__epoll.poll(timeout):
                default_action = None
                self.__log("event from epoll#%d for #%d:%d" % (self.__epoll.fileno(), fileno, events), verbosity=3)
                yield lambda: self.__callback[fileno](events)
        except InterruptedError:
            return
        if default_action is not None:
            yield default_action


class ClientSocket:
    def __init__(self, logger, epoll, connection, remote_addr, connector):
        self.__log = logger
        self.__epoll = epoll
        self.__socket = connection
        self.__remote_addr = remote_addr
        self.__buffer = b''
        self.__write_buffer = []
        self.__connector = connector(self)

        self.__socket.setblocking(False)
        self.__epoll.register(self.__socket, lambda events: self.__handle(events))

    def __handle(self, events):
        assert events
        if events & select.EPOLLIN:
            events &= ~ select.EPOLLIN
            while True:
                try:
                    data = self.__socket.recv(4096)
                except BlockingIOError:
                    break
                if not data:
                    self.__log("connection #%d closed" % self.__socket.fileno())
                    self.__epoll.unregister(self.__socket)
                    self.__socket.close()
                    break
                assert data
                self.__log("received from socket#%d: %s" % (self.__socket.fileno(), ' '.join('%02x' % x for x in data)),
                           verbosity=3)

                data = data.split(b'\n')
                for chunk in data[:-1]:
                    self.execute(self.__buffer + chunk)
                    self.__buffer = b''
                self.__buffer = data[-1]

        if events & select.EPOLLOUT:
            assert len(self.__write_buffer) == 0
            events &= ~ select.EPOLLOUT
        assert not events

    def write(self, data):
        if self.__write_buffer:
            self.__write_buffer.append(data)
            return
        r = self.__socket.send(data)
        if r == len(data):
            return
        self.__write_buffer.append(data[r:])

    def execute(self, command):
        self.__log("command from connection #%d: %s" % (self.__socket.fileno(), command.decode('iso8859-1')))
        self.__connector(command)


class ServerSocket:
    def __init__(self, logger, epoll, connector):
        self.__log = logger
        self.__epoll = epoll
        self.__connector = connector
        self.__socket = socket.socket(
            type=socket.SOCK_STREAM | socket.SOCK_CLOEXEC | socket.SOCK_NONBLOCK
        )
        self.__socket.bind(('127.0.0.1', config['port']))
        self.__socket.listen(5)
        self.__epoll.register(self.__socket, lambda events: self.__handle(events))

    def __handle(self, events):
        assert events
        if events & select.EPOLLIN:
            events &= ~ select.EPOLLIN
            while True:
                try:
                    client, remote_addr = self.__socket.accept()
                except BlockingIOError:
                    break
                print("accepted client [%s]: %s" % (remote_addr, client))
                ClientSocket(self.__log, self.__epoll, client, remote_addr, self.__connector)
        assert not events


salt = "ahThiodai0ohG1phokoo"
connection_id = 0

class Connector:
    def __init__(self, socket):
        global connection_id
        self.__id = connection_id
        connection_id += 1
        self.__socket = socket
        self.__local_id = 0
    def __call__(self, command):
        command = command.split()
        if command[0] == b'test':
            self.__socket.write(b"test ok\n")
        else:
            self.__socket.write(b"unknown command: " + command[0] + b"\n")


logger = Logger(verbosity=config["verbosity"])
with Server(logger) as server:
    epoll = Epoll(logger)
    server_socket = ServerSocket(logger, epoll, Connector)
    server.run([lambda: epoll.poll(timeout=0.5)])

