import random
import datetime as dt

from pycalver import version


def test_current_calver():
    v = version.current_calver()
    assert len(v) == 7
    assert v.startswith("v")
    assert v[1:].isdigit()


def test_bump_beta():
    calver      = version.current_calver()
    cur_version = calver + ".0001-beta"
    assert cur_version < version.incr(cur_version)
    assert version.incr(cur_version).endswith("-beta")
    assert version.incr(cur_version, release="alpha").endswith("-alpha")
    assert version.incr(cur_version, release="final").endswith("0002")


def test_bump_final():
    calver      = version.current_calver()
    cur_version = calver + ".0001"
    assert cur_version < version.incr(cur_version)
    assert version.incr(cur_version, release="alpha").endswith("-alpha")
    assert version.incr(cur_version, release="final").endswith("0002")
    assert version.incr(cur_version).endswith("0002")


def test_bump_future():
    future_date   = dt.datetime.today() + dt.timedelta(days=300)
    future_calver = future_date.strftime("v%Y%m")
    cur_version   = future_calver + ".0001"
    assert cur_version < version.incr(cur_version)


def test_bump_random(monkeypatch):
    cur_date    = dt.date.today()
    cur_version = cur_date.strftime("v%Y%m") + ".0001-dev"

    def _mock_current_calver():
        return cur_date.strftime("v%Y%m")

    monkeypatch.setattr(version, 'current_calver', _mock_current_calver)

    for i in range(1000):
        cur_date += dt.timedelta(days=int((1 + random.random()) ** 10))
        new_version = version.incr(
            cur_version, release=random.choice([None, "alpha", "beta", "rc", 'final'])
        )
        assert cur_version < new_version
        cur_version = new_version


def test_parse_version_info():
    version_str = "v201712.0001-alpha"
    version_nfo = version.parse_version_info(version_str)

    assert version_nfo.pep440_version == "201712.1a0"
    assert version_nfo.version        == "v201712.0001-alpha"
    assert version_nfo.calver         == "v201712"
    assert version_nfo.year           == "2017"
    assert version_nfo.month          == "12"
    assert version_nfo.build          == ".0001"
    assert version_nfo.release        == "-alpha"

    version_str = "v201712.0001"
    version_nfo = version.parse_version_info(version_str)

    assert version_nfo.pep440_version == "201712.1"
    assert version_nfo.version        == "v201712.0001"
    assert version_nfo.calver         == "v201712"
    assert version_nfo.year           == "2017"
    assert version_nfo.month          == "12"
    assert version_nfo.build          == ".0001"
    assert version_nfo.release is None


def test_readme_pycalver1():
    version_str  = "v201712.0001-alpha"
    version_info = version.PYCALVER_RE.match(version_str).groupdict()

    assert version_info == {
        'version'    : "v201712.0001-alpha",
        'calver'     : "v201712",
        'year'       : "2017",
        'month'      : "12",
        'build'      : ".0001",
        'build_no'   : "0001",
        'release'    : "-alpha",
        'release_tag': "alpha",
    }


def test_readme_pycalver2():
    version_str  = "v201712.0033"
    version_info = version.PYCALVER_RE.match(version_str).groupdict()

    assert version_info == {
        'version'    : "v201712.0033",
        'calver'     : "v201712",
        'year'       : "2017",
        'month'      : "12",
        'build'      : ".0033",
        'build_no'   : "0033",
        'release'    : None,
        'release_tag': None,
    }


def test_parse_error_empty():
    try:
        version.parse_version_info("")
        assert False
    except ValueError as err:
        pass


def test_parse_error_noprefix():
    try:
        version.parse_version_info("201809.0002")
        assert False
    except ValueError as err:
        pass


def test_parse_error_nopadding():
    try:
        version.parse_version_info("v201809.2b0")
        assert False
    except ValueError as err:
        pass
