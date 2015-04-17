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

if __name__ == "__main__":
    print(subprocess.Popen(
        args=["/bin/date"] + scripts["test_date"]["default_arguments"],
        executable='/bin/date',
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        # stderr=subprocess.PIPE,
        cwd='/'
    ).stdout.readlines())

