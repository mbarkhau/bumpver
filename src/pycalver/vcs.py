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
import logging
import tempfile
import subprocess as sp


log = logging.getLogger("pycalver.vcs")


class WorkingDirectoryIsDirtyException(Exception):

    def __init__(self, message):
        self.message = message


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
    def assert_nondirty(cls):
        status_output = sp.check_output(cls._STATUS_COMMAND)
        lines = [
            line.strip()
            for line in status_output.splitlines()
            if not line.strip().startswith(b"??")
        ]

        if lines:
            cleaned_output = b"\n".join(lines)
            cls_name = cls.__name__
            raise WorkingDirectoryIsDirtyException(
                f"{cls_name} working directory is not clean:\n{cleaned_output}"
            )


class Git(BaseVCS):

    _TEST_USABLE_COMMAND = ["git", "rev-parse", "--git-dir"]
    _COMMIT_COMMAND = ["git", "commit", "-F"]
    _STATUS_COMMAND = ["git", "status", "--porcelain"]

    @classmethod
    def tag(cls, name):
        sp.check_output(["git", "tag", name])


class Mercurial(BaseVCS):

    _TEST_USABLE_COMMAND = ["hg", "root"]
    _COMMIT_COMMAND = ["hg", "commit", "--logfile"]
    _STATUS_COMMAND = ["hg", "status", "-mard"]

    @classmethod
    def tag(cls, name):
        sp.check_output(["hg", "tag", name])


VCS = [Git, Mercurial]


def get_vcs(allow_dirty=False):
    for vcs in VCS:
        if not vcs.is_usable():
            continue

        if not allow_dirty:
            try:
                vcs.assert_nondirty()
            except WorkingDirectoryIsDirtyException as e:
                log.warn(
                    f"{e.message}\n\n"
                    f"Use --allow-dirty to override this if you know what you're doing."
                )
                raise

        return vcs

    return None
