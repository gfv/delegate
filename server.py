import itertools
import signal

__author__ = 'm'


class Server:
    def __init__(self, logger1, keys1, policy1):
        self.log = logger1
        self.keys = keys1
        self.policy = policy1
        self.epoll = None
        self.queue = None
        self.__finish = False
        self.__sleep = False
        self.__actions_start = []
        self.__actions_sleep = []
        # self.__actions_cron = []

        signal.signal(signal.SIGTERM, lambda signo, frame: self.__signal(signo))
        signal.signal(signal.SIGUSR1, lambda signo, frame: self.__signal(signo))
        signal.signal(signal.SIGCHLD, lambda signo, frame: self.__signal(signo))
        # TODO: more signals (HUP)

    def __signal(self, signo):
        if signo == signal.SIGTERM:
            # self.log("[SIGTERM]")
            self.__finish = True
        elif signo == signal.SIGUSR1:
            self.log.reopen()
            # self.log("logs rotated")
        elif signo == signal.SIGCHLD:
            self.wake()
            # self.log("caught SIGCHLD, ignore it")
        else:
            self.log("unknown signal: %d" % signo)
            self.__finish = True

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