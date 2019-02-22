import random
import datetime as dt

from pycalver import version
from pycalver import patterns


def test_bump_beta():
    cur_version = "v201712.0001-beta"
    assert cur_version < version.incr(cur_version)
    assert version.incr(cur_version).endswith("-beta")
    assert version.incr(cur_version, release="alpha").endswith("-alpha")
    assert version.incr(cur_version, release="final").endswith("0002")


def test_bump_final():
    cur_version = "v201712.0001"
    assert cur_version < version.incr(cur_version)
    assert version.incr(cur_version).endswith(".0002")
    assert version.incr(cur_version, release="alpha").endswith("-alpha")

    assert version.incr(cur_version, release="final").endswith(".0002")

    pre_version = cur_version + "-beta"
    assert version.incr(pre_version, release="final").endswith(".0002")


def test_bump_future():
    """Test that versions don't go back in time."""
    future_date   = dt.datetime.today() + dt.timedelta(days=300)
    future_calver = future_date.strftime("v%Y%m")
    cur_version   = future_calver + ".0001"
    new_version   = version.incr(cur_version)
    assert cur_version < new_version


def test_bump_random(monkeypatch):
    cur_date    = dt.date(2016, 1, 1) + dt.timedelta(days=random.randint(1, 2000))
    cur_version = cur_date.strftime("v%Y%m") + ".0001-dev"

    monkeypatch.setattr(version, 'TODAY', cur_date)

    for i in range(1000):
        cur_date += dt.timedelta(days=int((1 + random.random()) ** 10))
        new_version = version.incr(
            cur_version, release=random.choice([None, "alpha", "beta", "rc", "final", "post"])
        )
        assert cur_version < new_version
        cur_version = new_version


def test_parse_version_info():
    version_str = "v201712.0001-alpha"
    version_nfo = version.parse_version_info(version_str)

    # assert version_nfo.pep440_version == "201712.1a0"
    # assert version_nfo.version        == "v201712.0001-alpha"
    assert version_nfo.year  == 2017
    assert version_nfo.month == 12
    assert version_nfo.bid   == "0001"
    assert version_nfo.tag   == "alpha"

    version_str = "v201712.0001"
    version_nfo = version.parse_version_info(version_str)

    # assert version_nfo.pep440_version == "201712.1"
    # assert version_nfo.version        == "v201712.0001"
    assert version_nfo.year  == 2017
    assert version_nfo.month == 12
    assert version_nfo.bid   == "0001"
    assert version_nfo.tag   == "final"


def test_readme_pycalver1():
    version_str  = "v201712.0001-alpha"
    version_info = patterns.PYCALVER_RE.match(version_str).groupdict()

    assert version_info == {
        'pycalver'   : "v201712.0001-alpha",
        'vYYYYMM'    : "v201712",
        'year'       : "2017",
        'month'      : "12",
        'build'      : ".0001",
        'build_no'   : "0001",
        'release'    : "-alpha",
        'release_tag': "alpha",
    }


def test_readme_pycalver2():
    version_str  = "v201712.0033"
    version_info = patterns.PYCALVER_RE.match(version_str).groupdict()

    assert version_info == {
        'pycalver'   : "v201712.0033",
        'vYYYYMM'    : "v201712",
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


def test_part_field_mapping():
    a_names = set(version.PATTERN_PART_FIELDS.keys())
    b_names = set(patterns.PART_PATTERNS.keys())
    c_names = set(patterns.COMPOSITE_PART_PATTERNS.keys())

    extra_names = a_names - b_names
    assert not any(extra_names)
    missing_names = b_names - a_names
    assert missing_names == c_names

    a_fields = set(version.PATTERN_PART_FIELDS.values())
    b_fields = set(version.VersionInfo._fields)

    assert a_fields == b_fields
