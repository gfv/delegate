__author__ = 'm'


class Module:
    def __init__(self, server1):
        self._server = server1
        self._log = lambda *args, **kwargs: self._server.log(*args, **kwargs)