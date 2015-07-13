import hashlib
from config import config
from module import Module
from request import Request

__author__ = 'm'

connection_id = 0
salt_random = b""
with open('/dev/random', 'rb') as f:
    salt_random = f.read(32)

class Connector(Module):
    def __init__(self, server1, socket):
        super(Connector, self).__init__(server1)
        global connection_id  # , salt_random
        self.__id = connection_id
        self.__salt_random = salt_random
        with open('/dev/urandom', 'rb') as f:
            self.__salt_random += f.read(32)
        connection_id += 1
        self.__socket = socket
        self.__local_id = 0
        self.__hash = None
        self.salt1 = config["salt1"]
        self.salt2 = config["salt2"]

    def __run(self, command_key, command_hash, command_run):
        user_key = self._server.keys.get_user_key(command_key)
        if user_key is None:
            return self.__socket.write(b'unauthorized\n')
        real_key = user_key
        real_hash = hashlib.sha256(
            real_key + b':' + self.salt2 + b':' + self.__hash + b':' + b'%'.join(command_run)
        ).hexdigest().encode("ascii")
        self.__hash = None
        if command_hash != real_hash:
            return self.__socket.write(b'unauthorized\n')
        self._server.queue.append(Request(command_key, command_run[0], command_run[1:], self.__socket))

    def __call__(self, command):
        command = command.split()
        if len(command) == 0:
            return
        if command[0] == b'test' and len(command) == 1:
            self.__socket.write(b"test ok\n")
        elif command[0] == b'hello' and len(command) == 1:
            self.__hash = hashlib.sha256(
                self.salt1 + self.__salt_random + (":%d_%d" % (self.__id, self.__local_id)).encode("ascii")
            ).hexdigest().encode("ascii")
            self.__local_id += 1
            self.__socket.write(b"hello " + self.__hash + b"\n")
        elif command[0] == b"run" and len(command) > 3 and self.__hash is not None:
            self.__run(command[1], command[2], command[3:])
        else:
            self.__socket.write(b"unknown command: " + command[0] + b"\n")
