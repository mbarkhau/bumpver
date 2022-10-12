from __future__ import annotations

import os
import pathlib as pl
import shlex
import shutil
import subprocess as sp
import tempfile
from contextlib import ExitStack


class Shell:
    def __init__(self, cwd):
        self.cwd = cwd

    def __call__(self, cmd):
        if isinstance(cmd, str):
            cmd_parts = shlex.split(cmd)
        else:
            cmd_parts = cmd
        output = sp.check_output(cmd_parts, cwd=self.cwd, text=True)
        return output


_MODULE_PATH = pl.Path(__file__)
FIXTURES_DIR = _MODULE_PATH.parent / "fixtures"

FIXTURE_PATH_PARTS = [
    ["README.rst"],
    ["README.md"],
    ["setup.cfg"],
    ["setup.py"],
    ["pycalver.toml"],
    ["bumpver.toml"],
    ["src", "module_v1", "__init__.py"],
    ["src", "module_v2", "__init__.py"],
]


class _TmpCwd:
    def __init__(self, dir: os.PathLike | str) -> None:
        self.dir = dir
        self._original: str | None = None

    def __enter__(self) -> None:
        self._original = os.getcwd()
        os.chdir(self.dir)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._original is not None:
            os.chdir(self._original)
            self._original = None


class Project:
    def __init__(self, project=None):
        if project is not None and not project.startswith("project_"):
            project = f"project_{project}"
        self._project = project

        self._exit_stack = ExitStack()
        self.dir: pl.Path | None = None

    def _make_tmp(self) -> None:
        tmpdir = tempfile.TemporaryDirectory(prefix="pytest_")
        self._exit_stack.enter_context(tmpdir)

        self.dir = pl.Path(tmpdir.name) / "bumpver_project"
        self.dir.mkdir()

        if self._project is None:
            return

        fixtures_subdir = FIXTURES_DIR / self._project

        for path_parts in FIXTURE_PATH_PARTS:
            fixture_fpath = fixtures_subdir.joinpath(*path_parts)
            if fixture_fpath.exists():
                project_fpath = self.dir.joinpath(*path_parts)
                project_fpath.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(fixture_fpath, project_fpath)

    def __enter__(self):
        self._make_tmp()
        self._exit_stack.enter_context(_TmpCwd(self.dir))
        return self

    def __exit__(self, *exc):
        self._exit_stack.__exit__(*exc)
        return False

    def shell(self, cmd):
        shell = Shell(str(self.dir))
        return shell(cmd)

    def _vcs_addall(self, cmd):
        added_file_paths = []
        for path_parts in FIXTURE_PATH_PARTS:
            maybe_file_path = self.dir.joinpath(*path_parts)
            if maybe_file_path.exists():
                self.shell(cmd + " add " + str(maybe_file_path))
                added_file_paths.append(maybe_file_path)

        assert len(added_file_paths) >= 2

    def git_init(self):
        self.shell("git init")
        self._vcs_addall(cmd="git")
        self.shell("git commit -m 'initial commit'")

    def hg_init(self):
        self.shell("hg init")
        self._vcs_addall(cmd="hg")
        self.shell("hg commit -m 'initial commit'")
