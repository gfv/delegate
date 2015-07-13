import subprocess
from config import scripts
import os

__author__ = 'm'
# config file for scripts

def launch_script(request, policy):

    if b"ALLOW_ARGUMENTS" in policy.parameters and scripts[request.script.decode()]["need_arguments"]:
        arguments = request.arguments
    else:
        arguments = []

    if b"PROVIDE_USERNAME" in policy.parameters:
        os.environ["DELEGATE_USERNAME"] = policy.user

    process = subprocess.Popen(
        args=[scripts[request.script.decode()]["cmd_line"]] + scripts[request.script.decode()]["default_arguments"] + arguments,
        executable=scripts[request.script.decode()]["cmd_line"],
        stdin=open("/dev/null", "r"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd='/'
    )

    return process

