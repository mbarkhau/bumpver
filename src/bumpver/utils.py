# This file is part of the bumpver project
# https://github.com/mbarkhau/bumpver
#
# Copyright (c) 2018-2024 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import typing as typ
import datetime as dt
import functools

# NOTE (mb 2020-09-24): The main use of the memo function is
#   not as a performance optimization, but to reduce logging
#   spam.


def memo(func: typ.Callable) -> typ.Callable:
    cache = {}

    @functools.wraps(func)
    def wrapper(*args):
        key = str(args)
        if key not in cache:
            cache[key] = func(*args)
        return cache[key]

    return wrapper


def now() -> dt.datetime:
    if hasattr(dt, 'UTC'):
        return dt.datetime.now(dt.UTC)
    else:
        return dt.datetime.utcnow()
