# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import random
import datetime as dt

import pytest

from bumpver import version
from bumpver import v1version
from bumpver import v2version
from bumpver import v1patterns
from bumpver import v2patterns

# pylint:disable=protected-access ; allowed for test code


def test_bump_beta():
    cur_version = "v201712.0001-beta"
    assert cur_version < v1version.incr(cur_version)
    assert v1version.incr(cur_version).endswith("-beta")
    assert v1version.incr(cur_version, tag="alpha").endswith("-alpha")
    assert v1version.incr(cur_version, tag="final").endswith("0002")


def test_bump_final_v1():
    cur_version = "v201712.0001"
    assert cur_version < v1version.incr(cur_version)
    assert v1version.incr(cur_version).endswith(".0002")
    assert v1version.incr(cur_version, tag="alpha").endswith("-alpha")

    assert v1version.incr(cur_version, tag="final").endswith(".0002")

    pre_version = cur_version + "-beta"
    assert v1version.incr(pre_version, tag="final").endswith(".0002")


def test_bump_final_v2():
    print()
    raw_pattern = "vMAJOR.MINOR.PATCH[PYTAGNUM]"
    cur_version = "v0.1.4b1"
    assert v2version.incr(cur_version, raw_pattern, major=True  ) == "v1.0.0b0"
    assert v2version.incr(cur_version, raw_pattern, minor=True  ) == "v0.2.0b0"
    assert v2version.incr(cur_version, raw_pattern, patch=True  ) == "v0.1.5b0"
    assert v2version.incr(cur_version, raw_pattern, tag_num=True) == "v0.1.4b2"
    assert v2version.incr(cur_version, raw_pattern, patch=True, tag="final") == "v0.1.5"


def test_bump_future():
    """Test that versions don't go back in time."""
    future_date   = dt.datetime.today() + dt.timedelta(days=300)
    future_calver = future_date.strftime("v%Y%m")
    cur_version   = future_calver + ".0001"
    new_version   = v1version.incr(cur_version)
    assert cur_version < new_version


def test_bump_random(monkeypatch):
    cur_date    = dt.date(2016, 1, 1) + dt.timedelta(days=random.randint(1, 2000))
    cur_version = cur_date.strftime("v%Y%m") + ".0001-dev"

    monkeypatch.setattr(version, 'TODAY', cur_date)

    for _ in range(1000):
        cur_date += dt.timedelta(days=int((1 + random.random()) ** 10))
        new_version = v1version.incr(
            cur_version, tag=random.choice([None, "alpha", "beta", "rc", "final", "post"])
        )
        assert cur_version < new_version
        cur_version = new_version


def test_bump_tag_num():
    raw_pattern = "MAJOR.MINOR.PATCH[PYTAGNUM]"
    cur_version = "0.1.1b0"
    assert v2version.incr(cur_version, raw_pattern, tag_num=True) == "0.1.1b1"


def test_bump_tag_num_without_tag():
    raw_pattern = "MAJOR.MINOR.PATCH[PYTAGNUM]"
    cur_version = "0.1.1"
    assert v2version.incr(cur_version, raw_pattern, tag_num=True) is None


def test_parse_version_info():
    version_str  = "v201712.0001-alpha"
    version_info = v1version.parse_version_info(version_str)

    # assert version_info.pep440_version == "201712.1a0"
    # assert version_info.version        == "v201712.0001-alpha"
    assert version_info.year  == 2017
    assert version_info.month == 12
    assert version_info.bid   == "0001"
    assert version_info.tag   == "alpha"

    version_str  = "v201712.0001"
    version_info = v1version.parse_version_info(version_str)

    # assert version_info.pep440_version == "201712.1"
    # assert version_info.version        == "v201712.0001"
    assert version_info.year  == 2017
    assert version_info.month == 12
    assert version_info.bid   == "0001"
    assert version_info.tag   == "final"


def test_readme_pycalver1():
    version_str  = "v201712.0001-alpha"
    version_info = v1patterns.PYCALVER_RE.match(version_str).groupdict()

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
    version_info = v1patterns.PYCALVER_RE.match(version_str).groupdict()

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
        v1version.parse_version_info("")
        assert False
    except version.PatternError as err:
        assert "Invalid version string" in str(err)


def test_parse_error_noprefix():
    try:
        v1version.parse_version_info("201809.0002")
        assert False
    except version.PatternError as err:
        assert "Invalid version string" in str(err)


def test_parse_error_nopadding():
    try:
        v1version.parse_version_info("v201809.2b0")
        assert False
    except version.PatternError as err:
        assert "Invalid version string" in str(err)


def test_part_field_mapping_v1():
    a_names = set(v1patterns.PATTERN_PART_FIELDS.keys())
    b_names = set(v1patterns.PART_PATTERNS.keys())
    c_names = set(v1patterns.COMPOSITE_PART_PATTERNS.keys())

    a_extra_names = a_names - b_names
    assert not any(a_extra_names), sorted(a_extra_names)
    b_extra_names = b_names - (a_names | c_names)
    assert not any(b_extra_names), sorted(b_extra_names)

    a_fields = set(v1patterns.PATTERN_PART_FIELDS.values())
    b_fields = set(version.V1VersionInfo._fields)

    a_extra_fields = a_fields - b_fields
    b_extra_fields = b_fields - a_fields
    assert not any(a_extra_fields), sorted(a_extra_fields)
    assert not any(b_extra_fields), sorted(b_extra_fields)


def v1vnfo(**field_values):
    return v1version._parse_field_values(field_values)


def v2vnfo(**field_values):
    return v2version.parse_field_values_to_vinfo(field_values)


PARSE_V1_VERSION_TEST_CASES = [
    ["{year}.{month}.{dom}"            , "2017.06.07", v1vnfo(year="2017", month="06", dom="07")],
    ["{year}.{month}.{dom_short}"      , "2017.06.7" , v1vnfo(year="2017", month="06", dom="7" )],
    ["{year}.{month}.{dom_short}"      , "2017.06.7" , v1vnfo(year="2017", month="06", dom="7" )],
    ["{year}.{month_short}.{dom_short}", "2017.6.7"  , v1vnfo(year="2017", month="6" , dom="7" )],
    ["{year}.{month}.{dom}"            , "2017.6.07" , None],
    ["{year}.{month}.{dom}"            , "2017.06.7" , None],
    ["{year}.{month_short}.{dom}"      , "2017.06.7" , None],
    ["{year}.{month}.{dom_short}"      , "2017.6.07" , None],
    ["{year}.{month_short}.{MINOR}"    , "2017.6.7"  , v1vnfo(year="2017", month="6" , minor="7" )],
    ["{year}.{month}.{MINOR}"          , "2017.06.7" , v1vnfo(year="2017", month="06", minor="7" )],
    ["{year}.{month}.{MINOR}"          , "2017.06.07", v1vnfo(year="2017", month="06", minor="07")],
    ["{year}.{month}.{MINOR}"          , "2017.6.7"  , None],
    ["YYYY.0M.0D"                      , "2017.06.07", v2vnfo(year_y="2017", month="06", dom="07")],
    ["YYYY.MM.DD"                      , "2017.6.7"  , v2vnfo(year_y="2017", month="6" , dom="7" )],
    ["YYYY.MM.MD"                      , "2017.06.07", None],
    ["YYYY.0M.0D"                      , "2017.6.7"  , None],
]


@pytest.mark.parametrize("pattern_str, line, expected_vinfo", PARSE_V1_VERSION_TEST_CASES)
def test_v1_parse_versions(pattern_str, line, expected_vinfo):
    if "{" in pattern_str:
        pattern       = v1patterns.compile_pattern(pattern_str)
        version_match = pattern.regexp.search(line)
    else:
        pattern       = v2patterns.compile_pattern(pattern_str)
        version_match = pattern.regexp.search(line)

    if expected_vinfo is None:
        assert version_match is None
    else:
        assert version_match is not None

        version_str = version_match.group(0)

        if "{" in pattern_str:
            version_info = v1version.parse_version_info(version_str, pattern_str)
            assert version_info == expected_vinfo
        else:
            version_info = v2version.parse_version_info(version_str, pattern_str)
            assert version_info == expected_vinfo


def test_v2_parse_versions():
    _vnfo = v2version.parse_version_info("v201712.0033", raw_pattern="vYYYY0M.BUILD[-TAG[NUM]]")
    fvals = {'year_y': 2017, 'month': 12, 'bid': "0033"}
    assert _vnfo == v2version.parse_field_values_to_vinfo(fvals)


def test_v2_format_version():
    version_pattern = "vYYYY0M.BUILD[-TAG[NUM]]"
    in_version      = "v200701.0033-beta"

    vinfo       = v2version.parse_version_info(in_version, raw_pattern=version_pattern)
    out_version = v2version.format_version(vinfo, raw_pattern=version_pattern)
    assert in_version == out_version

    result = v2version.format_version(vinfo, raw_pattern="v0Y.BUILD[-TAG]")
    assert result == "v07.0033-beta"

    result = v2version.format_version(vinfo, raw_pattern="vYY.BLD[-TAG]")
    assert result == "v7.33-beta"

    result = v2version.format_version(vinfo, raw_pattern="vYY.BLD-TAG")
    assert result == "v7.33-beta"

    result = v2version.format_version(vinfo, raw_pattern='__version__ = "YYYY.BUILD[-TAG]"')
    assert result == '__version__ = "2007.0033-beta"'

    result = v2version.format_version(vinfo, raw_pattern='__version__ = "YYYY.BLD"')
    assert result == '__version__ = "2007.33"'


WEEK_PATTERN_TEXT_CASES = [
    ("YYYYWW.PATCH", True),
    ("YYYYUU.PATCH", True),
    ("GGGGVV.PATCH", True),
    ("YYWW.PATCH"  , True),
    ("YYUU.PATCH"  , True),
    ("GGVV.PATCH"  , True),
    ("0YWW.PATCH"  , True),
    ("0YUU.PATCH"  , True),
    ("0GVV.PATCH"  , True),
    ("0Y0W.PATCH"  , True),
    ("0Y0U.PATCH"  , True),
    ("0G0V.PATCH"  , True),
    ("GGGGWW.PATCH", False),
    ("GGGGUU.PATCH", False),
    ("YYYYVV.PATCH", False),
    ("GGWW.PATCH"  , False),
    ("GGUU.PATCH"  , False),
    ("YYVV.PATCH"  , False),
    ("0GWW.PATCH"  , False),
    ("0GUU.PATCH"  , False),
    ("0YVV.PATCH"  , False),
    ("0G0W.PATCH"  , False),
    ("0G0U.PATCH"  , False),
    ("0Y0V.PATCH"  , False),
]


@pytest.mark.parametrize("pattern, expected", WEEK_PATTERN_TEXT_CASES)
def test_is_valid_week_pattern(pattern, expected):
    assert v2version.is_valid_week_pattern(pattern) == expected
