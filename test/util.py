import os
import shlex
import shutil
import tempfile
import subprocess as sp

import pathlib2 as pl


class Shell:
    def __init__(self, cwd):
        self.cwd = cwd

    def __call__(self, cmd):
        if isinstance(cmd, str):
            cmd_parts = shlex.split(cmd)
        else:
            cmd_parts = cmd
        output = sp.check_output(cmd_parts, cwd=self.cwd)
        return output.decode("utf-8")


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


class Project:
    def __init__(self, project=None):
        tmpdir        = pl.Path(tempfile.mkdtemp(prefix="pytest_"))
        self.tmpdir   = tmpdir
        self.prev_cwd = os.getcwd()

        self.dir = tmpdir / "bumpver_project"
        self.dir.mkdir()

        if project is None:
            return

        if not project.startswith("project_"):
            project = "project_" + project

        fixtures_subdir = FIXTURES_DIR / project

        for path_parts in FIXTURE_PATH_PARTS:
            fixture_fpath = fixtures_subdir.joinpath(*path_parts)
            if fixture_fpath.exists():
                project_fpath = self.dir.joinpath(*path_parts)
                project_fpath.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(str(fixture_fpath), str(project_fpath))

    def __enter__(self):
        os.chdir(str(self.dir))
        return self

    def __exit__(self, *exc):
        shutil.rmtree(str(self.tmpdir))
        os.chdir(self.prev_cwd)
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
