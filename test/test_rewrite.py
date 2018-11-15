from pycalver import rewrite


REWRITE_FIXTURE = """
# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT

__version__ = "v201809.0002-beta"
"""


def test_rewrite_lines():
    old_lines   = REWRITE_FIXTURE.splitlines()
    patterns    = ['__version__ = "{version}"']
    new_version = "v201809.0003"
    new_lines   = rewrite.rewrite_lines(patterns, new_version, old_lines)

    assert len(new_lines) == len(old_lines)
    assert new_version not in "\n".join(old_lines)
    assert new_version     in "\n".join(new_lines)
