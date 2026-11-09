import errno
from c05_mlock_probe import probe, MIB


def fake_limit(limit_bytes):
    def try_lock(size):
        return 0 if size <= limit_bytes else errno.ENOMEM
    return try_lock


def test_stops_at_first_failure():
    result = probe([1, 8, 64, 512], fake_limit(8 * MIB))
    assert result == [(1, "OK"), (8, "OK"), (64, "ENOMEM")]


def test_all_pass_when_unlimited():
    assert probe([1, 8], fake_limit(10 ** 12)) == [(1, "OK"), (8, "OK")]


def test_eperm_is_reported_by_name():
    assert probe([1], lambda size: errno.EPERM) == [(1, "EPERM")]
