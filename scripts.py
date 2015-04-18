import subprocess

__author__ = 'm'
# config file for scripts

scripts = {
    "test": {
        "cmd_line": "/bin/echo",
        "need_arguments": True,
        "default_arguments": []
    },
    "test_date": {"cmd_line": "/bin/date",
                  "need_arguments": False,
                  "default_arguments": []
    },
    "test_date2": {
        "cmd_line": "/bin/date",
        "need_arguments": False,
        "default_arguments": ["+%s"]
    },
}


def launch_script(request, policy):
    if "ALLOW_ARGUMENTS" in policy.parameters and scripts[request.script]["need_arguments"]:
        arguments = request.arguments
    else:
        arguments = []
    process = subprocess.Popen(
        args=[request.script] + scripts["test_date"]["default_arguments"] + arguments,
        executable=request.script,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd='/'
    )
    return process

