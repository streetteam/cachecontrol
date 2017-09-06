from datetime import datetime

from mock import Mock
from cachecontrol.caches import RedisCache
from cachecontrol.cache import keymaker
import fakeredis
import pytest


class TestRedisCache(object):

    def setup(self):
        self.conn = Mock(spec=fakeredis.FakeStrictRedis())
        self.cache = RedisCache(self.conn)

    def test_set_expiration(self):
        self.cache.set('foo', 'bar', expires=datetime(2099, 2, 2))
        assert self.conn.setex.called


class TestRedisCacheGetSemantics(object):
    def setup(self):
        self.cache = RedisCache(fakeredis.FakeStrictRedis())

    def teardown(self):
        self.cache.clear()

    @pytest.mark.parametrize("key, value, expected", [
        ("key-a", 100, b'100'),
        ("key-b", 948, b'948'),
        ("key-b;deadbeef", 3, b'3'),
        ("this;other", 0, b'0'),
        ("key-b;other", '', b''),
    ])
    def test_get_returns_key_if_it_exists(self, key, value, expected):
        self.cache.set(key, value)
        assert self.cache.get(key) == expected

    def test_get_prefers_non_separated_key_if_both_are_set(self):
        # we use keys in two formats - url + url;some-identifier
        # if keys in both format are set we default to using the shorter format
        self.cache.set('this;and-that', 4)
        self.cache.set('this', 44)
        assert self.cache.get('this;and-that') == b'44'

    @pytest.mark.parametrize("prefix, suffix, prefix_value, combined_value, expected", [
        ("this", "other", 0, '', b'0'),
        ("this", "other", '', 0, b''),
        ("this", "other", False, 0, b'False'),
    ])
    def test_get_when_both_values_are_falsey(self, prefix, suffix, prefix_value, combined_value, expected):
        combined_key = keymaker(prefix, suffix)
        self.cache.set(prefix, prefix_value)
        self.cache.set(combined_key, combined_value)
        assert self.cache.get(combined_key) == expected

    @pytest.mark.parametrize("value_auth, value, expected_auth, expected", [
        (None, None, None, None),
        ('sensitive-data', None, b'sensitive-data', None),
        (None, 'foo', b'foo', b'foo'),
        ('sensitive-data', 'foo', b'foo', b'foo'),
    ])
    def test_get_set_matrix(self, value_auth, value, expected_auth, expected):
        if value_auth is not None:
            self.cache.set("url;auth-hash", value_auth)

        if value is not None:
            self.cache.set("url", value)

        assert self.cache.get("url;auth-hash") == expected_auth
        assert self.cache.get("url") == expected


class TestRedisCacheDeleteSemantics(object):
    def setup(self):
        self.cache = RedisCache(fakeredis.FakeStrictRedis())

    def teardown(self):
        self.cache.clear()

    def test_deleting_suffixed_key_also_deletes_short_key(self):
        self.cache.set('this;and-that', 4)
        self.cache.set('this', 44)
        self.cache.delete('this;and-that')
        assert self.cache.get('this') is None

    def test_deleting_short_key_deletes_all_suffixed_versions(self):
        self.cache.set('this;foobarbaz', 4)
        self.cache.set('this;and-that', 4)
        self.cache.set('this', 44)
        self.cache.delete('this')
        assert len(self.cache.keys()) == 0
