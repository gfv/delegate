import subprocess

__author__ = 'm'
# config file for scripts

scripts = {
    "test": {
        "cmd_line": "/bin/sleep",
        "need_arguments": True,
        "default_arguments": ["5"],
    },
    "test_date": {
        "cmd_line": "/bin/date",
        "need_arguments": False,
        "default_arguments": [],
    },
    "test_date2": {
        "cmd_line": "/bin/date",
        "need_arguments": False,
        "default_arguments": ["+%s"],
    },
}


def launch_script(request, policy):
    if b"ALLOW_ARGUMENTS" in policy.parameters and scripts[request.script.decode()]["need_arguments"]:
        arguments = request.arguments
    else:
        arguments = []
    process = subprocess.Popen(
        args=[scripts[request.script.decode()]["cmd_line"]] + scripts[request.script.decode()]["default_arguments"] + arguments,
        executable=scripts[request.script.decode()]["cmd_line"],
        # executable="/bin/date",
        stdin=open("/dev/null", "r"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd='/'
    )
    return process

