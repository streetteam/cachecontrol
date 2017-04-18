import pytest
from cachecontrol.cache import keymaker, keybreaker


@pytest.mark.parametrize('prefix, suffix', [
    ('thisisprefix', 'andthisissuffix'),
    ('thisisprefix', ''),
    ('', 'andthisissuffix'),
    ('', ''),
])
def test_keymaking_is_inverse_of_keybreaking(prefix, suffix):
    assert keybreaker(keymaker(prefix, suffix)) == (prefix, suffix)
