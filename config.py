__author__ = 'VK OPS CREW <ncc(at)vk.com>'

config = {
    'serve': '0.0.0.0',
    'port': 2390,
    'verbosity': 2,
    'salt1': b"ahThiodai0ohG1phokoo",
    'salt2': b"Aej1ohv8Naish5Siec3U",
    'path_to_users': 'users',
    'path_to_policies': 'policies',
}

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
