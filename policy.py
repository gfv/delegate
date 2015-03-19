__author__ = 'm'


class Policy:

    def __init__(self, user="", group="", parameters=[], script=""):
        self.user = user
        self.group = group
        self.parameters = parameters
        self.script = script


class PolicyManager:

    def __init__(self, key_manager, logger):
        self.policies = []
        self.users = {}
        self.groups = {}
        self.cmds = {}
        self.key_manager = key_manager
        self.log = logger

    def add_policy(self, policy):
        ok_user = False
        ok_group = False
        ok_script = False

        if policy.user != "":
            if not self.key_manager.has_user(policy.user):
                self.log.log("Can not find key for user %s" % str(policy.user), "E")
                return -1
            else:
                ok_user = True
        if policy.group != "":
            if not self.key_manager.has_group(policy.group):
                self.log.log("Can not find key for group %s" % str(policy.group), "E")
                return -1
            else:
                ok_group = True
        if ok_user and ok_group:
            self.log.log("Ambiguous rule. Use either user or group.", "E")
            return -1
        if policy.script != "":
            ok_script = True
        else:
            self.log.log("You should specify script to launch", "E")
            return -1
        if not ok_script:
            if policy.user in self.users:
                self.users[policy.user].append(policy)
            else:
                self.users[policy.user] = [policy]
            if policy.group in self.groups:
                self.groups[policy.group].append(policy)
            else:
                self.groups[policy.group] = [policy]
            if policy.script in self.cmds:
                self.cmds[policy.script].append(policy)
            else:
                self.cmds[policy.script] = [policy]
            self.policies.append(policy)

    def dump_policies(self):
        for policy in self.policies:
            result_string = ""
            if policy.user != "":
                result_string += "-u %s " % policy.user
            if policy.group != "":
                result_string += "-g %s " % policy.group
            for param in policy.parameters:
                result_string += "-p%s " % param
            result_string += policy.script + "\n"
            print(result_string)

    def check_request(self, request):
        if request.script not in self.cmds:
            return False
        key_to_check = request.signed_with
        if not self.key_manager.has_key(key_to_check):
            return False
        user_or_group = self.key_manager.get_subject_by_key(key_to_check)
        if user_or_group.group:
            for policy in self.cmds[request.script]:
                if user_or_group.name == policy.group:
                    if len(request.arguments) > 0:
                        if "ALLOW_ARGUMENTS" in policy.parameters:
                            return True
                        return False
                    else:
                        return True
            return False
        else:
            for policy in self.cmds[request.script]:
                if user_or_group.name == policy.user:
                    if len(request.arguments) > 0:
                        if "ALLOW_ARGUMENTS" in policy.parameters:
                            return True
                        return False
                    else:
                        return True
            return False


