import random
import datetime as dt

from pycalver import version


def test_current_calver():
    v = version.current_calver()
    assert len(v) == 7
    assert v.startswith("v")
    assert v[1:].isdigit()


def test_bump_beta():
    calver = version.current_calver()
    cur_version = calver + ".0001-beta"
    assert cur_version < version.bump(cur_version)
    assert version.bump(cur_version).endswith("-beta")
    assert version.bump(cur_version, release="alpha").endswith("-alpha")
    assert version.bump(cur_version, release="final").endswith("0002")


def test_bump_final():
    calver = version.current_calver()
    cur_version = calver + ".0001"
    assert cur_version < version.bump(cur_version)
    assert version.bump(cur_version, release="alpha").endswith("-alpha")
    assert version.bump(cur_version, release="final").endswith("0002")
    assert version.bump(cur_version).endswith("0002")


def test_bump_future():
    future_date = dt.datetime.today() + dt.timedelta(days=300)
    future_calver = future_date.strftime("v%Y%m")
    cur_version = future_calver + ".0001"
    assert cur_version < version.bump(cur_version)


def test_bump_random():
    cur_date = dt.date.today()
    cur_version = cur_date.strftime("v%Y%m") + ".0001-dev"

    def _mock_current_calver():
        return cur_date.strftime("v%Y%m")

    _orig_current_calver = version.current_calver
    version.current_calver = _mock_current_calver
    try:
        for i in range(1000):
            cur_date += dt.timedelta(days=int((1 + random.random()) ** 10))
            new_version = version.bump(cur_version, release=random.choice([
                None, "alpha", "beta", "rc", "final"
            ]))
            assert cur_version < new_version
            cur_version = new_version
    finally:
        version.current_calver = _orig_current_calver
