__author__ = 'm'


class Policy:

    def __init__(self, user=None, group=None, parameters=list(), script=""):
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

        if policy.user is not None:
            if self.key_manager.get_user_key(policy.user) is not None:
                self.log("Can not find key for user %s" % str(policy.user), "E")
                return -1
            else:
                ok_user = True
        #if policy.group is not None:
        #    if not self.key_manager.has_group(policy.group):
        #        self.log("Can not find key for group %s" % str(policy.group), "E")
        #        return -1
        #    else:
        ok_group = True
        if ok_user and ok_group:
            self.log("Ambiguous rule. Use either user or group.", "E")
            return -1
        if policy.script != "":
            ok_script = True
        else:
            self.log("You should specify script to launch", "E")
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
            self.log("Can't check execution policies for non-existing script %s" % request.script, "E")
            return False
        user_to_check = request.signed_with
        cmd_to_check = request.script
        if cmd_to_check in self.cmds:
            self.log("Checking permissions to execute %s" % cmd_to_check, "N", 3)
            policy = self.cmds[cmd_to_check]
            if user_to_check == policy.user:
                return policy
            elif policy.group is not None:
                groups = self.key_manager.get_user_groups(user_to_check)
                if policy.group in groups:
                    return policy
                else:
                    return False
            else:
                return False
        else:
            self.log("Can't check permissions for non-existing scripts %s" % cmd_to_check, "E")
            return False


