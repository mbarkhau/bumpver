# This file is part of the bumpver project
# https://github.com/mbarkhau/bumpver
#
# Copyright (c) 2018-2024 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path  # type: ignore

__all__ = ['Path']
