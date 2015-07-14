__author__ = 'VK OPS CREW <ncc(at)vk.com>'

class Request:
    def __init__(self, key, script, arguments, output):
        self.signed_with = key
        self.script = script
        self.arguments = arguments
        self.output = output
