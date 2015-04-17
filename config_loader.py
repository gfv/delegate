from policy import Policy

__author__ = 'm'


class ConfigLoader:
    def __init__(self, log, users_file, policies_file, policy_manager, key_manager):
        self.log = log
        self.users_file = users_file
        self.policies_file = policies_file
        self.policy_manager = policy_manager
        self.key_manager = key_manager

    def read(self):
        try:
            users_fd = open(self.users_file)
            policies_fd = open(self.policies_file)
        except IOError as e:
            pass
        for line in users_fd.readlines():
            l = line.strip().split(":")
            if len(l) > 2:
                self.log("More than one ':'?", "E")
                return
            if "group" in l[0][0:5]:
                self.key_manager.add_group(l[0].split(" ")[1])
                for u in l[1].strip().split(" "):
                    self.key_manager.add_group_member(u, l[0].split(" ")[1])
            else:
                self.key_manager.add_user(l[0].strip(), l[1].strip())
        users_fd.close()

        for line in policies_fd.readlines():
            tokens = line.split(" ")
            policy = Policy()
            prev_token = None
            for token in tokens:
                if token[0] == '-':
                    if token[1] == 'u':
                        pass
                    elif token[1] == 'g':
                        pass
                    elif token[1] == 'p':
                        policy.parameters.append(token[2:])
                else:
                    if prev_token == '-u':
                        policy.user = token
                    elif prev_token == '-g':
                        policy.group = token
                prev_token = token
            policy.script = tokens[-1]
            self.policy_manager.add_policy(policy)
        policies_fd.close()
