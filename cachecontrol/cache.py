"""
The cache object API for implementing caches. The default is a thread
safe in-memory dictionary.
"""
from threading import Lock


class BaseCache(object):

    def get(self, key):
        raise NotImplemented()

    def set(self, key, value):
        raise NotImplemented()

    def delete(self, key):
        raise NotImplemented()

    def close(self):
        pass


class DictCache(BaseCache):

    def __init__(self, init_dict=None):
        self.lock = Lock()
        self.data = init_dict or {}

    def get(self, key):
        return self.data.get(key, None)

    def set(self, key, value):
        with self.lock:
            self.data.update({key: value})

    def delete(self, key):
        with self.lock:
            if key in self.data:
                self.data.pop(key)


CACHE_KEY_DELIMTER = ';'


def keymaker(prefix, suffix=''):
    """Given a prefix and an optional suffix, create a cache key

    The purpose of the suffix and DELIMTER is to allow two kinds of cache key
    - public level keys that are available to all users and user level keys
    where the suffix is used to identify said user
    """
    fmt = "{}{}{}" if suffix else "{}"
    return fmt.format(prefix, CACHE_KEY_DELIMTER, suffix)


def keybreaker(key):
    """Given a cache key, return the prefix and suffix used to create it"""
    split = key.split(CACHE_KEY_DELIMTER)
    prefix = split[0]
    try:
        suffix = split[1]
    except IndexError:
        suffix = ''
    return prefix, suffix
