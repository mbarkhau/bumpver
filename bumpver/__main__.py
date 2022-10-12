# This file is part of the bumpver project
# https://github.com/mbarkhau/bumpver
#
# Copyright (c) 2018-2022 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""
__main__ module for BumpVer.

Enables use as module: $ python -m bumpver --version
"""
from __future__ import annotations

from . import cli

if __name__ == "__main__":
    cli.cli()
