# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT
#
# pycalver/vcs.py (this file) is based on code from the
# bumpversion project: https://github.com/peritus/bumpversion
# MIT License - (C) 2013-2014 Filip Noetzel

import os
import sys
import logging
import tempfile
import typing as typ
import subprocess as sp


log = logging.getLogger("pycalver.vcs")


class BaseVCS:

    @classmethod
    def commit(cls, message):
        f = tempfile.NamedTemporaryFile("wb", delete=False)
        f.write(message.encode("utf-8"))
        f.close()
        cmd = cls._COMMIT_COMMAND + [f.name]
        env_items = list(os.environ.items()) + [(b"HGENCODING", b"utf-8")]
        sp.check_output(cmd, env=dict(env_items))
        os.unlink(f.name)

    @classmethod
    def is_usable(cls):
        try:
            return sp.call(
                cls._TEST_USABLE_COMMAND,
                stderr=sp.PIPE,
                stdout=sp.PIPE,
            ) == 0
        except OSError as e:
            if e.errno == 2:
                # mercurial is not installed then, ok.
                return False
            raise

    @classmethod
    def dirty_files(cls):
        status_output = sp.check_output(cls._STATUS_COMMAND)
        return [
            line.decode("utf-8")[2:].strip()
            for line in status_output.splitlines()
            if not line.strip().startswith(b"??")
        ]

    @classmethod
    def assert_not_dirty(cls, filepaths: typ.Set[str], allow_dirty=False) -> None:
        dirty_files = cls.dirty_files()

        if dirty_files:
            log.warn(f"{cls.__name__} working directory is not clean:")
            for file in dirty_files:
                log.warn("    " + file)

        if not allow_dirty and dirty_files:
            sys.exit(1)

        dirty_pattern_files = set(dirty_files) & filepaths
        if dirty_pattern_files:
            log.error("Not commiting when pattern files are dirty:")
            for file in dirty_pattern_files:
                log.warn("    " + file)
            sys.exit(1)


class Git(BaseVCS):

    _TEST_USABLE_COMMAND = ["git", "rev-parse", "--git-dir"]
    _COMMIT_COMMAND = ["git", "commit", "-F"]
    _STATUS_COMMAND = ["git", "status", "--porcelain"]

    @classmethod
    def tag(cls, name):
        sp.check_output(["git", "tag", name])

    @classmethod
    def add_path(cls, path):
        sp.check_output(["git", "add", "--update", path])


class Mercurial(BaseVCS):

    _TEST_USABLE_COMMAND = ["hg", "root"]
    _COMMIT_COMMAND = ["hg", "commit", "--logfile"]
    _STATUS_COMMAND = ["hg", "status", "-mard"]

    @classmethod
    def tag(cls, name):
        sp.check_output(["hg", "tag", name])

    @classmethod
    def add_path(cls, path):
        pass


VCS = [Git, Mercurial]


def get_vcs():
    for vcs in VCS:
        if vcs.is_usable():
            return vcs

    return None
