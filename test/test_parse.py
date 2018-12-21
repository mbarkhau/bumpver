import re
from pycalver import parse


def test_re_pattern_parts():
    part_re_by_name = {
        part_name: re.compile(part_re_str)
        for part_name, part_re_str in parse.RE_PATTERN_PARTS.items()
    }

    cases = [
        ("pep440_version", "201712.31"          , "201712.31"),
        ("pep440_version", "v201712.0032"       , None),
        ("pep440_version", "201712.0033-alpha"  , None),
        ("version"       , "v201712.0034"       , "v201712.0034"),
        ("version"       , "v201712.0035-alpha" , "v201712.0035-alpha"),
        ("version"       , "v201712.0036-alpha0", "v201712.0036-alpha"),
        ("version"       , "v201712.0037-pre"   , "v201712.0037"),
        ("version"       , "201712.38a0"        , None),
        ("version"       , "201712.0039"        , None),
        ("calver"        , "v201712"            , "v201712"),
        ("calver"        , "v201799"            , "v201799"),  # maybe date validation should be a thing
        ("calver"        , "201712"             , None),
        ("calver"        , "v20171"             , None),
        ("build"         , ".0012"              , ".0012"),
        ("build"         , ".11012"             , ".11012"),
        ("build"         , ".012"               , None),
        ("build"         , "11012"              , None),
        ("release"       , "-alpha"             , "-alpha"),
        ("release"       , "-beta"              , "-beta"),
        ("release"       , "-dev"               , "-dev"),
        ("release"       , "-rc"                , "-rc"),
        ("release"       , "-post"              , "-post"),
        ("release"       , "-pre"               , ""),
        ("release"       , "alpha"              , ""),
    ]

    for part_name, line, expected in cases:
        part_re = part_re_by_name[part_name]
        result  = part_re.search(line)
        if result is None:
            assert expected is None, (part_name, line)
        else:
            result_val = result.group(0)
            assert result_val == expected, (part_name, line)


SETUP_PY_FIXTURE = """
# setup.py
import setuptools
__version__ = 'v201712.0002-alpha'
setuptools.setup(
...
   version='201712.2a0',
"""


def test_default_parse_patterns():
    lines    = SETUP_PY_FIXTURE.splitlines()
    patterns = ["{version}", "{pep440_version}"]

    matches = list(parse.iter_matches(lines, patterns))
    assert len(matches) == 2

    assert matches[0].lineno == 3
    assert matches[1].lineno == 6

    assert matches[0].pattern == patterns[0]
    assert matches[1].pattern == patterns[1]

    assert matches[0].match == "v201712.0002-alpha"
    assert matches[1].match == "201712.2a0"


def test_explicit_parse_patterns():
    lines = SETUP_PY_FIXTURE.splitlines()

    patterns = ["__version__ = '{version}'", "version='{pep440_version}'"]

    matches = list(parse.iter_matches(lines, patterns))
    assert len(matches) == 2

    assert matches[0].lineno == 3
    assert matches[1].lineno == 6

    assert matches[0].pattern == patterns[0]
    assert matches[1].pattern == patterns[1]

    assert matches[0].match == "__version__ = 'v201712.0002-alpha'"
    assert matches[1].match == "version='201712.2a0'"


README_RST_FIXTURE = """
:alt: PyPI version

.. |version| image:: https://img.shields.io/badge/CalVer-v201809.0002--beta-blue.svg
:target: https://calver.org/
:alt: CalVer v201809.0002-beta
"""


def test_badge_parse_patterns():
    lines = README_RST_FIXTURE.splitlines()

    patterns = ["badge/CalVer-{calver}{build}-{release}-blue.svg", ":alt: CalVer {version}"]

    matches = list(parse.iter_matches(lines, patterns))
    assert len(matches) == 2

    assert matches[0].lineno == 3
    assert matches[1].lineno == 5

    assert matches[0].pattern == patterns[0]
    assert matches[1].pattern == patterns[1]

    assert matches[0].match == "badge/CalVer-v201809.0002--beta-blue.svg"
    assert matches[1].match == ":alt: CalVer v201809.0002-beta"


CLI_MAIN_FIXTURE = """
@click.group()
@click.version_option(version="v201812.0123-beta")
@click.help_option()
"""


def test_pattern_escapes():
    pattern_re = parse.compile_pattern(r'click.version_option(version="{version}")')
    match      = pattern_re.search(CLI_MAIN_FIXTURE)
    assert match.group(0) == 'click.version_option(version="v201812.0123-beta")'


CURLY_BRACE_FIXTURE = """
package_metadata = {"name": "mypackage", "version": "v201812.0123-beta"}
"""


def test_curly_escapes():
    pattern    = r'package_metadata = {"name": "mypackage", "version": "{version}"}'
    pattern_re = parse.compile_pattern(pattern)
    match      = pattern_re.search(CURLY_BRACE_FIXTURE)
    assert (
        match.group(0) == 'package_metadata = {"name": "mypackage", "version": "v201812.0123-beta"}'
    )
