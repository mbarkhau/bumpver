# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT

import os

__version__ = "v201809.0002-beta"

DEBUG = os.environ.get("PYDEBUG", "0") == "1"
