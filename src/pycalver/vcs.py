# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# Copyright (c) 2018 Manuel Barkhau (@mbarkhau) - MIT License
# SPDX-License-Identifier: MIT
#
# pycalver/vcs.py (this file) is based on code from the
# bumpversion project: https://github.com/peritus/bumpversion
# Copyright (c) 2013-2014 Filip Noetzel - MIT License
"""Minimal Git and Mercirial API.

If terminology for similar concepts differs between git and
mercurial, then the git terms are used. For example "fetch"
(git) instead of "pull" (hg) .
"""

import os
import logging
import tempfile
import typing as typ
import subprocess as sp


log = logging.getLogger("pycalver.vcs")


VCS_SUBCOMMANDS_BY_NAME = {
    'git': {
        'is_usable': "git rev-parse --git-dir",
        'fetch'    : "git fetch",
        'ls_tags'  : "git tag --list v*",
        'status'   : "git status --porcelain",
        'add_path' : "git add --update {path}",
        'commit'   : "git commit --file {path}",
        'tag'      : "git tag --annotate {tag} --message {tag}",
        'push_tag' : "git push origin {tag}",
    },
    'hg': {
        'is_usable': "hg root",
        'fetch'    : "hg pull",
        'ls_tags'  : "hg tags",
        'status'   : "hg status -mard",
        'add_path' : "hg add {path}",
        'commit'   : "hg commit --logfile",
        'tag'      : "hg tag {tag} --message {tag}",
        'push_tag' : "hg push {tag}",
    },
}


class VCS:
    """VCS absraction for git and mercurial."""

    def __init__(self, name: str, subcommands: typ.Dict[str, str] = None):
        self.name = name
        if subcommands is None:
            self.subcommands = VCS_SUBCOMMANDS_BY_NAME[name]
        else:
            self.subcommands = subcommands

    def __call__(self, cmd_name: str, env=None, **kwargs: str) -> str:
        """Invoke subcommand and return output."""
        cmd_str     = self.subcommands[cmd_name]
        cmd_parts   = cmd_str.format(**kwargs).split()
        output_data = sp.check_output(cmd_parts, env=env)

        # TODO (mb 2018-11-15): Detect encoding of output?
        _encoding = "utf-8"
        return output_data.decode(_encoding)

    @property
    def is_usable(self) -> bool:
        """Detect availability of subcommand."""
        cmd = self.subcommands['is_usable'].split()

        try:
            retcode = sp.call(cmd, stderr=sp.PIPE, stdout=sp.PIPE)
            return retcode == 0
        except OSError as e:
            if e.errno == 2:
                # git/mercurial is not installed.
                return False
            raise

    def fetch(self) -> None:
        """Fetch updates from remote origin."""
        self('fetch')

    def status(self) -> typ.List[str]:
        """Get status lines."""
        status_output = self('status')
        return [
            line[2:].strip()
            for line in status_output.splitlines()
            if not line.strip().startswith("??")
        ]

    def ls_tags(self) -> typ.List[str]:
        """List vcs tags on all branches."""
        ls_tag_lines = self('ls_tags').splitlines()
        log.debug(f"ls_tags output {ls_tag_lines}")
        return [line.strip() for line in ls_tag_lines if line.strip().startswith("v")]

    def add(self, path: str) -> None:
        """Add updates to be included in next commit."""
        log.info(f"{self.name} add {path}")
        self('add_path', path=path)

    def commit(self, message: str) -> None:
        """Commit added files."""
        log.info(f"{self.name} commit -m '{message}'")
        message_data = message.encode("utf-8")

        tmp_file = tempfile.NamedTemporaryFile("wb", delete=False)
        assert " " not in tmp_file.name

        with tmp_file as fh:
            fh.write(message_data)

        env = os.environ.copy()
        # TODO (mb 2018-09-04): check that this works on py27,
        #   might need to be bytes there, idk.
        env['HGENCODING'] = "utf-8"
        self('commit', env=env, path=tmp_file.name)
        os.unlink(tmp_file.name)

    def tag(self, tag_name: str) -> None:
        """Create an annotated tag."""
        self('tag', tag=tag_name)

    def push(self, tag_name: str) -> None:
        """Push changes to origin."""
        self('push_tag', tag=tag_name)

    def __repr__(self) -> str:
        """Generate string representation."""
        return f"VCS(name='{self.name}')"


def get_vcs() -> VCS:
    """Detect the appropriate VCS for a repository.

    raises OSError if the directory doesn't use a supported VCS.
    """
    for vcs_name in VCS_SUBCOMMANDS_BY_NAME.keys():
        vcs = VCS(name=vcs_name)
        if vcs.is_usable:
            return vcs

    raise OSError("No such directory .git/ or .hg/ ")
