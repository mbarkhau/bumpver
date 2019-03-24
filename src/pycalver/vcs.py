# This file is part of the pycalver project
# https://gitlab.com/mbarkhau/pycalver
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
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
        'is_usable'   : "git rev-parse --git-dir",
        'fetch'       : "git fetch",
        'ls_tags'     : "git tag --list",
        'status'      : "git status --porcelain",
        'add_path'    : "git add --update {path}",
        'commit'      : "git commit --file {path}",
        'tag'         : "git tag --annotate {tag} --message {tag}",
        'push_tag'    : "git push origin {tag}",
        'show_remotes': "git config --get remote.origin.url",
    },
    'hg': {
        'is_usable'   : "hg root",
        'fetch'       : "hg pull",
        'ls_tags'     : "hg tags",
        'status'      : "hg status -umard",
        'add_path'    : "hg add {path}",
        'commit'      : "hg commit --logfile {path}",
        'tag'         : "hg tag {tag} --message {tag}",
        'push_tag'    : "hg push {tag}",
        'show_remotes': "hg paths",
    },
}


Env = typ.Dict[str, str]


class VCS:
    """VCS absraction for git and mercurial."""

    def __init__(self, name: str, subcommands: typ.Dict[str, str] = None):
        self.name = name
        if subcommands is None:
            self.subcommands = VCS_SUBCOMMANDS_BY_NAME[name]
        else:
            self.subcommands = subcommands

    def __call__(self, cmd_name: str, env: Env = None, **kwargs: str) -> str:
        """Invoke subcommand and return output."""
        cmd_tmpl = self.subcommands[cmd_name]
        cmd_str  = cmd_tmpl.format(**kwargs)
        if cmd_name in ("commit", "tag", "push_tag"):
            log.info(cmd_str)
        else:
            log.debug(cmd_str)
        output_data: bytes = sp.check_output(cmd_str.split(), env=env, stderr=sp.STDOUT)

        # TODO (mb 2018-11-15): Detect encoding of output?
        _encoding = "utf-8"
        return output_data.decode(_encoding)

    @property
    def is_usable(self) -> bool:
        """Detect availability of subcommand."""
        if not os.path.exists(f".{self.name}"):
            return False

        cmd = self.subcommands['is_usable'].split()

        try:
            retcode = sp.call(cmd, stderr=sp.PIPE, stdout=sp.PIPE)
            return retcode == 0
        except OSError as e:
            if e.errno == 2:
                # git/mercurial is not installed.
                return False
            raise

    @property
    def has_remote(self) -> bool:
        try:
            output = self('show_remotes')
            if output.strip() == "":
                return False
            return True
        except Exception:
            return False

    def fetch(self) -> None:
        """Fetch updates from remote origin."""
        if self.has_remote:
            self('fetch')

    def status(self, required_files: typ.Set[str]) -> typ.List[str]:
        """Get status lines."""
        status_output = self('status')
        status_items  = [line.split(" ", 1) for line in status_output.splitlines()]

        return [
            filepath.strip()
            for status, filepath in status_items
            if filepath.strip() in required_files or status != "??"
        ]

    def ls_tags(self) -> typ.List[str]:
        """List vcs tags on all branches."""
        ls_tag_lines = self('ls_tags').splitlines()
        log.debug(f"ls_tags output {ls_tag_lines}")
        return [line.strip().split(" ", 1)[0] for line in ls_tag_lines]

    def add(self, path: str) -> None:
        """Add updates to be included in next commit."""
        try:
            self('add_path', path=path)
        except sp.CalledProcessError as ex:
            if "already tracked!" in str(ex):
                # mercurial
                return
            else:
                raise

    def commit(self, message: str) -> None:
        """Commit added files."""
        message_data = message.encode("utf-8")

        tmp_file = tempfile.NamedTemporaryFile("wb", delete=False)
        assert " " not in tmp_file.name

        fh: typ.IO[bytes]

        with tmp_file as fh:
            fh.write(message_data)

        env: Env = os.environ.copy()
        env['HGENCODING'] = "utf-8"
        self('commit', env=env, path=tmp_file.name)
        os.unlink(tmp_file.name)

    def tag(self, tag_name: str) -> None:
        """Create an annotated tag."""
        self('tag', tag=tag_name)

    def push(self, tag_name: str) -> None:
        """Push changes to origin."""
        if self.has_remote:
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
