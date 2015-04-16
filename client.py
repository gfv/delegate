#!/usr/bin/env python3

import hashlib, socket, sys

target = "127.0.0.1:2390"
salt2 = b"Aej1ohv8Naish5Siec3U";
key_id = b"burunduk3";
key_value = b"abacabadabacaba";
# key_value = b"invalid_password";

host, port = target.split(':', 1)
port = int(port)

server_buffer = b''
server = socket.create_connection((host, port))

def query(data = None):
    global server, server_buffer
    if data is not None:
        r = 0
        data += b'\n'
        while r < len(data):
            r += server.send(data[r:])
    if b'\n' not in server_buffer:
        while True:
            data = server.recv(2048)
            assert len(data) > 0
            server_buffer += data
            if b'\n' in data:
                break
    result, server_buffer = server_buffer.split(b'\n', 1)
    return result

hello = query(b'hello')
result, key = hello.split()
assert result == b'hello'

command = [b'test', b'123']
command_hash = hashlib.sha256(
    key_value + b':' + salt2 + b':' + key + b':' + b'%'.join(command)
).hexdigest().encode("ascii")
started = query(b'run ' + key_id + b' ' + command_hash + b' ' + b' '.join(command))
if started != b'started':
    print("run fail: %s" % started.decode('iso8859-1'), file=sys.stderr)
    sys.exit(1)

print("[request send]")
while True:
    log = query()
    if log == b'FINISH':
        break
    if log.startswith(b'LOG: '):
        log = log[5:]
    print(log.decode('iso8859-1'))

