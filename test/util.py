import shlex
import shutil
import tempfile
import pathlib2 as pl
import subprocess as sp


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


class Project:
    def __init__(self, project_prefix="a"):
        if not project_prefix.endswith("_"):
            project_prefix += "_"

        tmpdir      = pl.Path(tempfile.mkdtemp(prefix="pytest_"))
        self.tmpdir = tmpdir

        _project_dir = tmpdir / "pycalver_project"
        _project_dir.mkdir()

        for fpath in FIXTURES_DIR.glob(project_prefix + "*"):
            fname = fpath.name[len(project_prefix) :]
            shutil.copy(fpath, _project_dir / fname)

        self.dir = _project_dir

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        shutil.rmtree(str(self.tmpdir))
        return False

    def sh(self, cmd):
        shell = Shell(str(self.dir))
        return shell(cmd)

    def git_init(self):
        self.sh("git init")
        self.sh("git add pycalver.toml")
        self.sh("git add README.md")
        self.sh("git commit -m 'initial commit'")

    def hg_init(self):
        self.sh = Shell(str(self.dir))
        self.sh("hg init")
        self.sh("hg add pycalver.toml")
        self.sh("hg add README.md")
        self.sh("hg commit -m 'initial commit'")
