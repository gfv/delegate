__author__ = 'm'

from policy import Policy
import os


class PolicyExecutor:

    def __init__(self, policy_manager, logger):
        self.policy_manager = policy_manager
        self.log = logger

    def execute_request_or_die(self, request):
        if self.policy_manager.check_request(request):
            pass
        else:
            self.log("Failed to execute request", "E")
            return -1