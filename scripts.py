__author__ = 'm'
# config file for scripts
import os


scripts = {
    "test": {"cmd_line": "/bin/echo", "need_arguments": True, "default_arguments": []},
}

if __name__ == "__main__":
    try:
        os.execv(str(scripts["test"]["cmd_line"]), ["", "Hello!"])
    except OSError as e:
        print(e)
