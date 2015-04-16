#!/usr/bin/env python3

__author__ = 'burunduk3'

import hashlib
import itertools
import select
import signal
import socket

from logger import Logger
from keys import KeyManager
from policy import PolicyManager
from config import config


class Server:
    def __init__(self, logger, keys, policy):
        self.log = logger
        self.keys = keys
        self.policy = policy
        self.epoll = None
        self.queue = None
        self.__finish = False
        self.__sleep = False
        self.__actions_start = []
        self.__actions_sleep = []
        # self.__actions_cron = []

        signal.signal(signal.SIGTERM, lambda signo, frame: self.__signal(signo))
        signal.signal(signal.SIGUSR1, lambda signo, frame: self.__signal(signo))
        # TODO: more signals (HUP)

    def __signal(self, signo):
        if signo == signal.SIGTERM:
            self.log("[SIGTERM]")
            self.__finish = True
        elif signo == signal.SIGUSR1:
            self.log.reopen()
            self.log("logs rotated")

    def action_add(self, action):
        self.__actions_start.append(action)

    def action_sleep_add(self, action):
        self.__actions_sleep.append(action)

    def wake(self):
        self.__sleep = False

    def run(self):
        actions = []
        try:
            while True:
                actions = list(actions)
                if not actions:
                    if self.__finish:
                        break
                    if self.__sleep:
                        actions.extend(self.__actions_sleep)
                    self.__sleep = True
                    actions.extend(self.__actions_start)
                self.log("actions: %s" % actions, verbosity=5)
                continuations = [action() for action in actions]
                actions = itertools.chain(*filter(lambda x: x is not None, continuations))
        except KeyboardInterrupt:
            self.log("[Ctrl+C]")
        self.log("TODO: graceful exit (close all sockets etc)")

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGUSR1, signal.SIG_DFL)
        self.log("TODO: close all sockets")


class Module:
    def __init__(self, server):
        self._server = server
        self._log = lambda *args, **kwargs: self._server.log(*args, **kwargs)

class Epoll(Module):
    def __init__(self, server):
        super().__init__(server)
        self.__epoll = select.epoll(flags=select.EPOLL_CLOEXEC)
        self.__callback = {}
        self.__timeout = 0
        self.__default_timeout = 0.5
        self._server.epoll = self
        self._server.action_add(lambda: self.poll())
        self._server.action_sleep_add(lambda: self.sleep())

    def sleep(self):
        self.__timeout = self.__default_timeout

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

    def poll(self):
        self._log("poll from epoll#%d" % self.__epoll.fileno(), verbosity=4)
        try:
            for fileno, events in self.__epoll.poll(self.__timeout):
                self.__timeout = 0
                self._server.wake()
                self._log("event from epoll#%d for #%d:%d" % (self.__epoll.fileno(), fileno, events), verbosity=3)
                yield lambda: self.__callback[fileno](events)
        except InterruptedError:
            pass


class ClientSocket(Module):
    def __init__(self, server, connection, remote_addr, connector):
        super().__init__(server)
        self.__socket = connection
        self.__remote_addr = remote_addr
        self.__buffer = b''
        self.__write_buffer = []
        self.__connector = connector(server, self)

        self.__socket.setblocking(False)
        self._server.epoll.register(self.__socket, lambda events: self.__handle(events))

    def __handle(self, events):
        assert events
        if events & select.EPOLLIN:
            events &= ~ select.EPOLLIN
            while True:
                try:
                    data = self.__socket.recv(4096)
                except ConnectionResetError:
                    data = None
                except BlockingIOError:
                    break
                if data is None or not data:
                    self._log("connection #%d closed" % self.__socket.fileno())
                    self._server.epoll.unregister(self.__socket)
                    self.__socket.close()
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
        self._log("command from connection #%d: %s" % (self.__socket.fileno(), command.decode('iso8859-1')))
        self.__connector(command)


class ServerSocket(Module):
    def __init__(self, server, connector):
        super().__init__(server)
        self.__connector = connector
        self.__socket = socket.socket(
            type=socket.SOCK_STREAM | socket.SOCK_CLOEXEC | socket.SOCK_NONBLOCK
        )
        self.__socket.bind(('127.0.0.1', config['port']))
        self.__socket.listen(5)
        self._server.epoll.register(self.__socket, lambda events: self.__handle(events))

    def __handle(self, events):
        assert events
        if events & select.EPOLLIN:
            events &= ~ select.EPOLLIN
            while True:
                try:
                    client, remote_addr = self.__socket.accept()
                except BlockingIOError:
                    break
                self._log("accepted client [%s]: %s" % (remote_addr, client))
                ClientSocket(self._server, client, remote_addr, self.__connector)
        assert not events


class Request:
    def __init__(self, key, script, arguments, output):
       self.signed_with = key
       self.script = script
       self.arguments = arguments
       self.output = output


salt = b"ahThiodai0ohG1phokoo"
salt2 = b"Aej1ohv8Naish5Siec3U"
salt_random = b""
connection_id = 0
keys = None

class Connector(Module):
    def __init__(self, server, socket):
        super().__init__(server)
        global connection_id
        self.__id = connection_id
        connection_id += 1
        self.__socket = socket
        self.__local_id = 0
        self.__hash = None
        self.__keys = keys

    def __run(self, command_key, command_hash, command_run):
        user_key = self._server.keys.get_user_key(command_key.decode('iso8859-1'))
        if user_key is None:
            return self.__socket.write(b'unauthorized\n')
        real_key = user_key.encode("ascii")
        real_hash = hashlib.sha256(
            real_key + b':' + salt2 + b':' + self.__hash + b':' + b'%'.join(command_run)
        ).hexdigest().encode("ascii")
        self.__hash = None
        if command_hash != real_hash:
            return self.__socket.write(b'unauthorized\n')
        self.__socket.write(b'started\n')
        self._server.queue.append(Request(command_key, command_run[0], command_run[1:], self.__socket))

    def __call__(self, command):
        global salt, salt2
        command = command.split()
        if len(command) == 0:
            return
        if command[0] == b'test' and len(command) == 1:
            self.__socket.write(b"test ok\n")
        elif command[0] == b'hello' and len(command) == 1:
            self.__hash = hashlib.sha256(
                salt + salt_random + (":%d_%d" % (self.__id, self.__local_id)).encode("ascii")
            ).hexdigest().encode("ascii")
            self.__local_id += 1
            self.__socket.write(b"hello " + self.__hash + b"\n")
        elif command[0] == b"run" and len(command) > 3 and self.__hash is not None:
            self.__run(command[1], command[2], command[3:])
        else:
            self.__socket.write(b"unknown command: " + command[0] + b"\n")


class RequestQueue(Module):
    def __init__(self, server):
        super().__init__(server)
        self._server.queue = self
        self.__queue = []
        self.__active = None
        self._server.action_add(lambda: self.run_next())
    def append(self, request):
        self.__queue.append(request)
    def run_next(self):
        if self.__active is not None or len(self.__queue) == 0:
            return
        self._server.wake()
        request = self.__queue[0]
        self.__queue = self.__queue[1:] # TODO: optimize
        yield lambda: self.__run(request)
    def __run(self, request):
        self.__active = request
        self._log("TODO: check and run " + (request.script + b' ' + b' '.join(request.arguments)).decode("iso8859-1"))
        request.output.write(b'LOG: test log, no action\n')
        request.output.write(b'FINISH\n')
        self.__active = None


logger = Logger(verbosity=config["verbosity"])
with open('/dev/random', 'rb') as f:
    salt_random = f.read(32)
keys = KeyManager(logger)
keys.add_user('burunduk3', 'abacabadabacaba')
policy = PolicyManager(keys, logger)
with Server(logger, keys, policy) as server:
    epoll, queue = Epoll(server), RequestQueue(server)
    server_socket = ServerSocket(server, Connector)
    logger("server started")
    server.run()

