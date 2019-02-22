import copy

from pycalver import config
from pycalver import rewrite

from . import util


REWRITE_FIXTURE = """
# SPDX-License-Identifier: MIT
__version__ = "v201809.0002-beta"
"""


def test_rewrite_lines():
    old_lines = REWRITE_FIXTURE.splitlines()
    patterns  = ['__version__ = "{pycalver}"']
    new_lines = rewrite.rewrite_lines(patterns, "v201911.0003", old_lines)

    assert len(new_lines) == len(old_lines)
    assert "v201911.0003" not in "\n".join(old_lines)
    assert "v201911.0003" in "\n".join(new_lines)


def test_rewrite_final():
    # Patterns written with {release_tag} placeholder preserve
    # the release tag even if the new version is -final

    old_lines = REWRITE_FIXTURE.splitlines()
    patterns  = ['__version__ = "v{year}{month}.{build_no}-{release_tag}"']
    new_lines = rewrite.rewrite_lines(patterns, "v201911.0003", old_lines)

    assert len(new_lines) == len(old_lines)
    assert "v201911.0003" not in "\n".join(old_lines)
    assert "None" not in "\n".join(new_lines)
    assert "v201911.0003-final" in "\n".join(new_lines)


def test_iter_file_paths():
    with util.Project(project="a") as project:
        ctx = config.init_project_ctx(project.dir)
        cfg = config.parse(ctx)
        assert cfg

        file_paths = {
            str(file_path) for file_path, patterns in rewrite._iter_file_paths(cfg.file_patterns)
        }

    assert file_paths == {"pycalver.toml", "README.md"}


def test_iter_file_globs():
    with util.Project(project="b") as project:
        ctx = config.init_project_ctx(project.dir)
        cfg = config.parse(ctx)
        assert cfg

        file_paths = {
            str(file_path) for file_path, patterns in rewrite._iter_file_paths(cfg.file_patterns)
        }

    assert file_paths == {
        "setup.cfg",
        "setup.py",
        "README.rst",
        "src/module_v1/__init__.py",
        "src/module_v2/__init__.py",
    }


def test_error_bad_path():
    with util.Project(project="b") as project:
        ctx = config.init_project_ctx(project.dir)
        cfg = config.parse(ctx)
        assert cfg

        (project.dir / "setup.py").unlink()
        try:
            list(rewrite._iter_file_paths(cfg.file_patterns))
            assert False, "expected ValueError"
        except ValueError as ex:
            assert "setup.py" in str(ex)


def test_error_bad_pattern():
    with util.Project(project="b") as project:
        ctx = config.init_project_ctx(project.dir)
        cfg = config.parse(ctx)
        assert cfg

        patterns = copy.deepcopy(cfg.file_patterns)
        patterns["setup.py"] = patterns["setup.py"][0] + "invalid"

        try:
            list(rewrite.diff("v201809.1234", patterns))
            assert False, "expected ValueError"
        except ValueError as ex:
            assert "setup.py" in str(ex)
