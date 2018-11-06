from pycalver import rewrite


def test_rewrite_lines():
    old_lines = [
        "# This file is part of the pycalver project",
        "# https://github.com/mbarkhau/pycalver",
        "#",
        "# (C) 2018 Manuel Barkhau (@mbarkhau)",
        "# SPDX-License-Identifier: MIT",
        '',
        "import os",
        '',
        '__version__ = "v201809.0002-beta"',
        'DEBUG = os.environ.get("PYDEBUG", "0") == "1"',
    ]
    patterns    = ['__version__ = "{version}"']
    new_version = "v201809.0003"
    new_lines   = rewrite.rewrite_lines(old_lines, patterns, new_version)

    assert len(new_lines) == len(old_lines)
    assert new_version not in "\n".join(old_lines)
    assert new_version     in "\n".join(new_lines)
