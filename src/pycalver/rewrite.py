#!/usr/bin/env python
# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT

import logging
import difflib

log = logging.getLogger("pycalver.rewrite")


def rewrite_file(file: str, pattern: str, dry=False) -> None:
    difflib.unified_diff(
        file_content_before.splitlines(),
        file_content_after.splitlines(),
        lineterm="",
        fromfile="a/" + file,
        tofile="b/" + file,
    )
