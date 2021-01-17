#!/usr/bin/env python
# This file is part of the bumpver project
# https://github.com/mbarkhau/bumpver
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""
__main__ module for BumpVer.

Enables use as module: $ python -m bumpver --version
"""
from . import cli

if __name__ == '__main__':
    cli.cli()
