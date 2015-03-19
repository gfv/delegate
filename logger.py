__author__ = 'mihver1'
import time


class Logger:

    def __init__(self, outfile):
        self.writer = open(outfile, "a")

    def log(self, message, type_="L"):
        result_string = ""
        result_string += str(time.time())
        result_string += ":%s: " % type_
        result_string += str(message)
        result_string += "\n"
        self.writer.write(result_string)

