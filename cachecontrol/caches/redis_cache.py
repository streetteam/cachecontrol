from __future__ import division

from datetime import datetime
from cachecontrol.cache import BaseCache, keybreaker


def total_seconds(td):
    """Python 2.6 compatability"""
    if hasattr(td, 'total_seconds'):
        return int(td.total_seconds())

    ms = td.microseconds
    secs = (td.seconds + td.days * 24 * 3600)
    return int((ms + secs * 10**6) / 10**6)


class RedisCache(BaseCache):

    def __init__(self, conn):
        self.conn = conn

    def get(self, key):
        # a key might be of the format foo;bar (where `;` is our default delimter).
        # To get this key's value from redis we do `mget foo foo;bar` (this
        # returns a list of values for each key searched for) and return the
        # first match
        key_prefix, _ = keybreaker(key)
        values = self.conn.mget([key_prefix, key])
        return values[0] if values[0] is not None else values[1]

    def set(self, key, value, expires=None):
        if not expires:
            self.conn.set(key, value)
        else:
            expires = expires - datetime.now()
            self.conn.setex(key, total_seconds(expires), value)

    def delete(self, key):
        prefix, _ = keybreaker(key)
        for key in self.keys("{}*".format(prefix)):
            self.conn.delete(key)

    def clear(self):
        """Helper for clearing all the keys in a database. Use with
        caution!"""
        for key in self.keys():
            self.conn.delete(key)

    def close(self):
        """Redis uses connection pooling, no need to close the connection."""
        pass

    def keys(self, pattern="*"):
        return self.conn.keys(pattern)
