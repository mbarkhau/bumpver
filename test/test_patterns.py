# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import re

import pytest

from bumpver import v1patterns
from bumpver import v2patterns

V2_PART_PATTERN_CASES = [
    (['YYYY', 'GGGG'], "2020" , "2020"),
    (['YYYY', 'GGGG'], ""     , None),
    (['YYYY', 'GGGG'], "A020" , None),
    (['YYYY', 'GGGG'], "020"  , None),
    (['YYYY', 'GGGG'], "12020", None),
    (['YY'  , 'GG'  ], "20"   , "20"),
    (['YY'  , 'GG'  ], "3"    , "3"),
    (['YY'  , 'GG'  ], "03"   , None),
    (['YY'  , 'GG'  ], "2X"   , None),
    (['YY'  , 'GG'  ], ""     , None),
    (['0Y'  , '0G'  ], "20"   , "20"),
    (['0Y'  , '0G'  ], "03"   , "03"),
    (['0Y'  , '0G'  ], "3"    , None),
    (['0Y'  , '0G'  ], "2X"   , None),
    (['0Y'  , '0G'  ], ""     , None),
    # quarter
    (['Q'], "0", None),
    (['Q'], "1", "1"),
    (['Q'], "2", "2"),
    (['Q'], "3", "3"),
    (['Q'], "4", "4"),
    (['Q'], "5", None),
    (['Q'], "X", None),
    # months
    (['MM'], "0" , None),
    (['MM'], "01", None),
    (['MM'], "1" , "1"),
    (['MM'], "10", "10"),
    (['MM'], "12", "12"),
    (['MM'], "13", None),
    (['0M'], "00", None),
    (['0M'], "1" , None),
    (['0M'], "01", "01"),
    (['MM'], "10", "10"),
    (['MM'], "12", "12"),
    (['MM'], "13", None),
    # day of month
    (['DD'], "0" , None),
    (['DD'], "01", None),
    (['DD'], "1" , "1"),
    (['DD'], "10", "10"),
    (['DD'], "31", "31"),
    (['DD'], "32", None),
    (['0D'], "00", None),
    (['0D'], "1" , None),
    (['0D'], "01", "01"),
    (['0D'], "10", "10"),
    (['0D'], "31", "31"),
    (['0D'], "32", None),
    (['DD'], "0" , None),
    (['DD'], "01", None),
    (['DD'], "1" , "1"),
    (['DD'], "10", "10"),
    (['DD'], "31", "31"),
    (['DD'], "32", None),
    (['0D'], "00", None),
    (['0D'], "1" , None),
    (['0D'], "01", "01"),
    (['0D'], "10", "10"),
    (['0D'], "31", "31"),
    (['0D'], "32", None),
    # day of year
    (['JJJ'], "0"  , None),
    (['JJJ'], "01" , None),
    (['JJJ'], "1"  , "1"),
    (['JJJ'], "10" , "10"),
    (['JJJ'], "31" , "31"),
    (['JJJ'], "32" , "32"),
    (['JJJ'], "100", "100"),
    (['JJJ'], "365", "365"),
    (['JJJ'], "366", "366"),
    (['JJJ'], "367", None),
    (['00J'], "000", None),
    (['00J'], "01" , None),
    (['00J'], "1"  , None),
    (['00J'], "001", "001"),
    (['00J'], "010", "010"),
    (['00J'], "031", "031"),
    (['00J'], "032", "032"),
    (['00J'], "100", "100"),
    (['00J'], "365", "365"),
    (['00J'], "366", "366"),
    (['00J'], "367", None),
    # week numbers
    (['WW', 'UU'], "00", None),
    (['WW', 'UU'], "01", None),
    (['WW', 'UU'], "0" , "0"),
    (['WW', 'UU'], "1" , "1"),
    (['WW', 'UU'], "10", "10"),
    (['WW', 'UU'], "52", "52"),
    (['WW', 'UU'], "53", None),
    (['0W', '0U'], "00", "00"),
    (['0W', '0U'], "01", "01"),
    (['0W', '0U'], "0" , None),
    (['0W', '0U'], "1" , None),
    (['0W', '0U'], "10", "10"),
    (['0W', '0U'], "52", "52"),
    (['0W', '0U'], "53", None),
    (['VV'], "00", None),
    (['VV'], "01", None),
    (['VV'], "0" , None),
    (['VV'], "1" , "1"),
    (['VV'], "10", "10"),
    (['VV'], "52", "52"),
    (['VV'], "53", "53"),
    (['VV'], "54", None),
    (['0V'], "00", None),
    (['0V'], "01", "01"),
    (['0V'], "0" , None),
    (['0V'], "1" , None),
    (['0V'], "10", "10"),
    (['0V'], "52", "52"),
    (['0V'], "53", "53"),
    (['0V'], "54", None),
    (['MAJOR', 'MINOR', 'PATCH'], "0", "0"),
    (['TAG'  ], "alpha" , "alpha"),
    (['TAG'  ], "alfa"  , None),
    (['TAG'  ], "beta"  , "beta"),
    (['TAG'  ], "rc"    , "rc"),
    (['TAG'  ], "post"  , "post"),
    (['TAG'  ], "final" , "final"),
    (['TAG'  ], "latest", None),
    (['PYTAG'], "a"     , "a"),
    (['PYTAG'], "b"     , "b"),
    (['PYTAG'], "rc"    , "rc"),
    (['PYTAG'], "post"  , "post"),
    (['PYTAG'], "post"  , "post"),
    (['PYTAG'], "x"     , None),
    (['NUM'  ], "a"     , None),
    (['NUM'  ], "0"     , "0"),
    (['NUM'  ], "1"     , "1"),
    (['NUM'  ], "10"    , "10"),
]


def _compile_part_re(pattern_str):
    grouped_pattern_str = r"^(?:" + pattern_str + r")$"
    # print("\n", grouped_pattern_str)
    return re.compile(grouped_pattern_str, flags=re.MULTILINE)


@pytest.mark.parametrize("parts, testcase, expected", V2_PART_PATTERN_CASES)
def test_v2_part_patterns(parts, testcase, expected):
    for part in parts:
        part_re = _compile_part_re(v2patterns.PART_PATTERNS[part])
        match   = part_re.match(testcase)
        if match is None:
            assert expected is None
        else:
            assert match.group(0) == expected


@pytest.mark.parametrize("part_name", v2patterns.PART_PATTERNS.keys())
def test_v1_part_compilation(part_name):
    assert _compile_part_re(v2patterns.PART_PATTERNS[part_name])


@pytest.mark.parametrize("part_name", v1patterns.PART_PATTERNS.keys())
def test_v2_part_compilation(part_name):
    assert _compile_part_re(v1patterns.PART_PATTERNS[part_name])


PATTERN_PART_CASES = [
    ("pep440_pycalver", "201712.31"          , "201712.31"),
    ("pep440_pycalver", "v201712.0032"       , None),
    ("pep440_pycalver", "201712.0033-alpha"  , None),
    ("pycalver"       , "v201712.0034"       , "v201712.0034"),
    ("pycalver"       , "v201712.0035-alpha" , "v201712.0035-alpha"),
    ("pycalver"       , "v201712.0036-alpha0", None),
    ("pycalver"       , "v201712.0037-pre"   , None),  # pre not available for v1 patterns
    ("pycalver"       , "201712.38a0"        , None),
    ("pycalver"       , "201712.0039"        , None),
    ("semver"         , "1.23.456"           , "1.23.456"),
    ("calver"         , "v201712"            , "v201712"),
    ("calver"         , "v201799"            , None),  # invalid date
    ("calver"         , "201712"             , None),
    ("calver"         , "v20171"             , None),
    ("build"          , ".0012"              , ".0012"),
    ("build"          , ".11012"             , ".11012"),
    ("build"          , ".012"               , None),
    ("build"          , "11012"              , None),
    ("release"        , "-alpha"             , "-alpha"),
    ("release"        , "-beta"              , "-beta"),
    ("release"        , "-dev"               , "-dev"),
    ("release"        , "-rc"                , "-rc"),
    ("release"        , "-post"              , "-post"),
    ("release"        , "-pre"               , None),  # pre not available for v1 patterns
    ("release"        , "alpha"              , None),  # missing dash "-" prefix
]


@pytest.mark.parametrize("part_name, line, expected", PATTERN_PART_CASES)
def test_v1_re_pattern_parts(part_name, line, expected):
    part_re = _compile_part_re(v1patterns.PART_PATTERNS[part_name])
    result  = part_re.match(line)
    if result is None:
        assert expected is None, (part_name, line, result)
    else:
        result_val = result.group(0)
        assert result_val == expected, (part_name, line)


PATTERN_V1_CASES = [
    (r"v{year}.{month}.{MINOR}"      , "v2017.11.1" , "v2017.11.1"),
    (r"v{year}.{month}.{MINOR}"      , "v2017.07.12", "v2017.07.12"),
    (r"v{year}.{month_short}.{PATCH}", "v2017.11.1" , "v2017.11.1"),
    (r"v{year}.{month_short}.{PATCH}", "v2017.7.12" , "v2017.7.12"),
]


@pytest.mark.parametrize("pattern_str, line, expected", PATTERN_V1_CASES)
def test_v1_patterns(pattern_str, line, expected):
    pattern = v1patterns.compile_pattern(pattern_str)
    result  = pattern.regexp.search(line)
    if result is None:
        assert expected is None, (pattern_str, line)
    else:
        result_val = result.group(0)
        assert result_val == expected, (pattern_str, line)


PATTERN_V2_CASES = [
    ("vYYYY.0M.MINOR" , "v2017.11.1" , "v2017.11.1"),
    ("vYYYY.0M.MINOR" , "v2017.07.12", "v2017.07.12"),
    ("YYYY.MM[.PATCH]", "2017.11.1"  , "2017.11.1"),
    ("YYYY.MM[.PATCH]", "2017.7.12"  , "2017.7.12"),
    ("YYYY.MM[.PATCH]", "2017.7"     , "2017.7"),
    ("YYYY0M.BUILD"   , "201707.1000", "201707.1000"),
]


@pytest.mark.parametrize("pattern_str, line, expected", PATTERN_V2_CASES)
def test_v2_patterns(pattern_str, line, expected):
    pattern    = v2patterns.compile_pattern(pattern_str)
    result     = pattern.regexp.search(line)
    result_val = None if result is None else result.group(0)
    assert result_val == expected, (pattern_str, line, pattern.regexp.pattern)


CLI_MAIN_FIXTURE = """
@click.group()
@click.version_option(version="v201812.0123-beta")
@click.help_option()
"""


def test_pattern_escapes():
    pattern_str = 'click.version_option(version="{pycalver}")'
    pattern     = v1patterns.compile_pattern(pattern_str)
    match       = pattern.regexp.search(CLI_MAIN_FIXTURE)
    expected    = 'click.version_option(version="v201812.0123-beta")'
    assert match.group(0) == expected


CURLY_BRACE_FIXTURE = """
package_metadata = {"name": "mypackage", "version": "v201812.0123-beta"}
"""


def test_curly_escapes():
    pattern_str = 'package_metadata = {"name": "mypackage", "version": "{pycalver}"}'
    pattern     = v1patterns.compile_pattern(pattern_str)
    match       = pattern.regexp.search(CURLY_BRACE_FIXTURE)
    expected    = 'package_metadata = {"name": "mypackage", "version": "v201812.0123-beta"}'
    assert match.group(0) == expected


def test_part_field_mapping_v2():
    a_names = set(v2patterns.PATTERN_PART_FIELDS.keys())
    b_names = set(v2patterns.PART_PATTERNS.keys())

    a_extra_names = a_names - b_names
    assert not any(a_extra_names), sorted(a_extra_names)
    b_extra_names = b_names - a_names
    assert not any(b_extra_names), sorted(b_extra_names)
