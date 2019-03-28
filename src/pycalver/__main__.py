#!/usr/bin/env python
# This file is part of the pycalver project
# https://gitlab.com/mbarkhau/pycalver
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""
__main__ module for PyCalVer.

Enables use as module: $ python -m pycalver --version
"""

if __name__ == '__main__':
    from . import cli

    cli.cli()
