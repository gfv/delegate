__author__ = 'm'
import hashlib


class KeyManager:

    def __init__(self, salt):
        self.__salt__ = salt

    def has_user(self, user):
        pass

    def has_group(self, group):
        pass

    def get_subject_by_key(self, key):
        pass

    def has_key(self, key):
        pass
