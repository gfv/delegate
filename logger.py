__author__ = 'mihver1'
import sys
import time


class Logger:

    def __init__(self, outfile=None, verbosity=0):
        self.__name = outfile
        self.writer = sys.stderr if self.__name is None else open(self.__name, "a")
        self.__verbosity = verbosity

    def __call__(self, message, type_="L", verbosity=0):
        if self.__verbosity < verbosity:
            return
        result_string = "[%s]:%s:%s\n" % (time.strftime("%Y-%m-%d %H:%M:%S %Z"), type_, message)
        self.writer.write(result_string)
        self.writer.flush()

    def log(self, message, type_="L", verbosity=0):
        self.__call__(message, type_, verbosity)

    def reopen(self):
        self.writer = sys.stderr if self.__name is None else open(self.__name, "a")

