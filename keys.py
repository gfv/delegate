__author__ = 'm'
import hashlib


class Key:
    def __init__(self):
        self.name = None
        self.key = None
        self.type = None


class Subject:
    def __init__(self):
        self.group = False
        self.user = False
        self.name = None


class KeyManager:
    def __init__(self, salt, logger):
        self.__salt__ = salt  # not used yet
        self.log = logger
        self.__keys__ = dict()
        self.__users__ = dict()
        self.__groups__ = dict()

    def add_key(self, key, type_, name):
        hashed_key = str(hashlib.sha256("%s%s" % (str(key), str(self.__salt__))).hexdigest())
        key_to_store = Key()
        key_to_store.key = hashed_key
        if type_ != "group" and type_ != "user":
            self.log("Can't recognise type of added key", "E")
            return -1
        key_to_store.type = type_
        if name == "" or name is None:
            self.log("Empty key name", "E")
            return -1
        key_to_store.name = name
        self.__keys__[hashed_key] = key_to_store
        if type_ == "user":
            self.__users__[name] = key_to_store
        elif type_ == "group":
            self.__groups__[name] = key_to_store
        else:
            self.log("WTF just happened?", "E", 0)
            return -1
        return 0

    def has_user(self, user):
        return bool(user in self.__users__)

    def has_group(self, group):
        return bool(group in self.__groups__)

    def get_subject_by_key(self, key):
        result = Subject()
        if key in self.__keys__:
            result.name = self.__keys__[key].name
            if self.__keys__[key].name in self.__users__:
                result.user = True
            elif self.__keys__[key].name in self.__groups__:
                result.group = True
        return result

    def has_key(self, key):
        return bool(key in self.__keys__)

    def get_key(self, name):
        return "abacadabacaba"
