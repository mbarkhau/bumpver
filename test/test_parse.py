# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

from bumpver import parse
from bumpver import v1patterns

SETUP_PY_FIXTURE = """
# setup.py
import setuptools
__version__ = 'v201712.0002-alpha'
setuptools.setup(
...
   version='201712.2a0',
"""


def test_default_parse_patterns():
    lines       = SETUP_PY_FIXTURE.splitlines()
    patterns    = ["{pycalver}", "{pep440_pycalver}"]
    re_patterns = [v1patterns.compile_pattern(p) for p in patterns]
    matches     = list(parse.iter_matches(lines, re_patterns))
    assert len(matches) == 2

    assert matches[0].lineno == 3
    assert matches[1].lineno == 6

    assert matches[0].pattern == re_patterns[0]
    assert matches[1].pattern == re_patterns[1]

    assert matches[0].match == "v201712.0002-alpha"
    assert matches[1].match == "201712.2a0"


def test_explicit_parse_patterns():
    lines = SETUP_PY_FIXTURE.splitlines()

    patterns    = ["__version__ = '{pycalver}'", "version='{pep440_pycalver}'"]
    re_patterns = [v1patterns.compile_pattern(p) for p in patterns]
    matches     = list(parse.iter_matches(lines, re_patterns))
    assert len(matches) == 2

    assert matches[0].lineno == 3
    assert matches[1].lineno == 6

    assert matches[0].pattern == re_patterns[0]
    assert matches[1].pattern == re_patterns[1]

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

    patterns    = ["badge/CalVer-{calver}{build}-{release}-blue.svg", ":alt: CalVer {pycalver}"]
    re_patterns = [v1patterns.compile_pattern(p) for p in patterns]
    matches     = list(parse.iter_matches(lines, re_patterns))

    assert len(matches) == 2

    assert matches[0].lineno == 3
    assert matches[1].lineno == 5

    assert matches[0].pattern == re_patterns[0]
    assert matches[1].pattern == re_patterns[1]

    assert matches[0].match == "badge/CalVer-v201809.0002--beta-blue.svg"
    assert matches[1].match == ":alt: CalVer v201809.0002-beta"
