import fcntl
import os
import select
from module import Module
from scripts import launch_script

__author__ = 'VK OPS CREW <ncc(at)vk.com>'


class RequestQueue(Module):
    def __init__(self, server1):
        super(RequestQueue, self).__init__(server1)
        self._server.queue = self
        self.__queue = []
        self.__active = None
        self._server.action_add(self._continue(self.run_next, ()))

    def append(self, request):
        self.__queue.append(request)
        self._log("New request, in queue: %d" % len(self.__queue))

    def __communicate(self, handle = None):
        if handle is None:
            assert self.__active is not None
            for x in [self.__active.stdout, self.__active.stderr]:
                self.__communicate(x)
            return
        while True:
            if self.__active is None:
                return
            # try:
            data = handle.read()
            # except ConnectionResetError:
            #     data = None
            # except BlockingIOError:
            #     break
            if data is None or not data:
                break
            self._log("read: '%s'" % str(data))
            assert data
            self._log("received from process: %s" % (' '.join('%02x' % x for x in data)),
                      verbosity=3)
            data = data.split(b'\n')
            for chunk in data[:-1]:
                self.__active.output.write(b'LOG: ' + self.__active.data + chunk + b'\n')
                self.__active.data = b''
            self.__active.data = data[-1]

    def run_next(self):
        if self.__active is not None:
            finished = self.__active.process.poll()
            if finished is None:
                return
            self._log('subprocess poll: %s' % str(finished), "D", 3)
            self._server.wake()
            self.__communicate()
            if self.__active.data:
                self.__active.output.write(b'LOG: ' + self.__active.data + b'%[noeoln]\n')
            self.__active.output.write(b'FINISH\n')
            self._log('Active cleared, in queue: %d' % len(self.__queue), "D", 3)
            self._server.epoll.unregister(self.__active.stdout)
            self._server.epoll.unregister(self.__active.stderr)
            self.__active.stdout.close()
            self.__active.stderr.close()
            self.__active = None
            return
        assert self.__active is None
        if len(self.__queue) == 0:
            return
        self._server.wake()
        request = self.__queue[0]
        self.__queue = self.__queue[1:]  # TODO: optimize
        yield self._continue(self.__run, (request ,))

    def __handle(self, handle, events):
        assert events
        if events & select.EPOLLIN:
            events &= ~ select.EPOLLIN
            self.__communicate(handle)
        if events & select.EPOLLHUP:
            events &= ~ select.EPOLLHUP
            yield self._continue(self.run_next, ())
        if events:
            self._log("unhandled poll events: 0x%04x\n" % events, "D", 3)
        assert not events

    def __run(self, request):
        if self.__active is not None:
            self.__queue.append(request)
            return
        assert self.__active is None
        self.__active = request
        access = self._server.policy.check_request(request)
        if access is False:
            request.output.write(b'access_denied\n')
            self.__active = None
            return
        request.output.write(b'started\n')
        request.process = launch_script(request, access)
        request.data = b''
        request.stdout = request.process.stdout
        request.stderr = request.process.stderr
        fl = fcntl.fcntl(request.stdout, fcntl.F_GETFL)
        fcntl.fcntl(request.stdout, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        fl = fcntl.fcntl(request.stderr, fcntl.F_GETFL)
        fcntl.fcntl(request.stderr, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        self._server.epoll.register(request.stdout, lambda events: self.__handle(request.stdout, events))
        self._server.epoll.register(request.stderr, lambda events: self.__handle(request.stderr, events))


