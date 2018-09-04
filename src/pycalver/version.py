# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT

import logging
import typing as typ
import datetime as dt

from . import lex_id
from . import parse

log = logging.getLogger("pycalver.version")


def current_calver() -> str:
    return dt.date.today().strftime("v%Y%m")


def bump(old_version: str, *, release: str=None) -> str:
    # old_version is assumed to be a valid calver string,
    # validated in pycalver.config.parse.
    old_ver = parse.parse_version_info(old_version)

    new_calver = current_calver()

    if old_ver.calver > new_calver:
        log.warning(
            f"'version.bump' called with '{old_version}', " +
            f"which is from the future, " +
            f"maybe your system clock is out of sync."
        )
        # leave calver as is (don't go back in time)
        new_calver = old_ver.calver

    new_build = lex_id.next_id(old_ver.build[1:])
    new_release: typ.Optional[str] = None

    if release is None:
        if old_ver.release:
            # preserve existing release
            new_release = old_ver.release[1:]
        else:
            new_release = None
    elif release == "final":
        new_release = None
    else:
        new_release = release

    new_version = new_calver + "." + new_build
    if new_release:
        new_version += "-" + new_release
    return new_version
