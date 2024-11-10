# This file is part of the bumpver project
# https://github.com/mbarkhau/bumpver
#
# Copyright (c) 2018-2024 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import os
import sys
import logging
import subprocess as sp

from bumpver import pathlib as pl

logger = logging.getLogger("bumpver.hooks")


def run(path: str, old_version: str, new_version: str) -> None:
    env = dict(os.environ, BUMPVER_OLD_VERSION=old_version, BUMPVER_NEW_VERSION=new_version)

    try:
        # Python2 compatibility
        # pylint:disable=consider-using-with
        proc = sp.Popen(str(pl.Path(path).absolute()), env=env, stdout=sp.PIPE, stderr=sp.PIPE)
        if proc.stdout is not None:
            with proc.stdout as out:
                for line in iter(out.readline, b''):
                    logger.info(f"\t{line.decode('utf8').strip()}")
        if proc.stderr is not None:
            with proc.stderr as err:
                for line in iter(err.readline, b''):
                    logger.error(f"\t{line.decode('utf8').strip()}")
        proc.wait()
    except IOError as err:
        logger.error(f"\t{err}")
        logger.error("Script exited with an error. Stopping")
        sys.exit(1)

    if proc.returncode != 0:
        logger.error("Script exited with an error. Stopping")
        sys.exit(1)
