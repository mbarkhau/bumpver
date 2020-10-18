#!/usr/bin/env python
# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# Copyright (c) 2018-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""
__main__ module for BumpVer.

Enables use as module: $ python -m bumpver --version
"""
from . import cli

if __name__ == '__main__':
    cli.cli()
