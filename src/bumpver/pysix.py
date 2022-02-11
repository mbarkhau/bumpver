# This file is part of the bumpver project
# https://github.com/mbarkhau/bumpver
#
# Copyright (c) 2018-2022 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import sys
import typing as typ

PY2 = sys.version_info.major < 3


try:
    from urllib.parse import quote as py3_stdlib_quote
except ImportError:
    from urllib import quote as py2_stdlib_quote  # type: ignore


# NOTE (mb 2016-05-23): quote in python2 expects bytes argument.


def quote(
    string  : str,
    safe    : str = "/",
    encoding: typ.Optional[str] = None,
    errors  : typ.Optional[str] = None,
) -> str:
    if not isinstance(string, str):
        errmsg = f"Expected str/unicode but got {type(string)}"  # type: ignore
        raise TypeError(errmsg)

    if encoding is None:
        _encoding = "utf-8"
    else:
        _encoding = encoding

    if errors is None:
        _errors = "strict"
    else:
        _errors = errors

    if PY2:
        data = string.encode(_encoding)

        res = py2_stdlib_quote(data, safe=safe.encode(_encoding))
        return res.decode(_encoding, errors=_errors)
    else:
        return py3_stdlib_quote(string, safe=safe, encoding=_encoding, errors=_errors)
