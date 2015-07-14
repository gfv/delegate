#!/usr/bin/env python3

__author__ = 'VK OPS CREW <ncc(at)vk.com>'

from config import config


salt1 = config["salt1"]
salt2 = config["salt2"]
# salt_random = b""
connection_id = 0
# keys = None

if __name__ == "__main__":
    from logger import Logger
    from keys import KeyManager
    from policy import PolicyManager
    from config_loader import ConfigLoader
    from auth import Connector
    from epoll import Epoll
    from request_queue import RequestQueue
    from server import Server
    from sockets import ServerSocket

    logger = Logger(verbosity=config["verbosity"])
    keys = KeyManager(logger)
    policy = PolicyManager(keys, logger)
    loader = ConfigLoader(logger, config["path_to_users"], config["path_to_policies"], policy, keys)
    loader.read()
    logger(policy.dump_policies())

    with Server(logger, keys, policy) as server:
        epoll, queue = Epoll(server), RequestQueue(server)
        server_socket = ServerSocket(server, Connector)
        logger("Server started")
        server.run()

