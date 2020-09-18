# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import copy
from test import util

from pycalver import config
from pycalver import rewrite as v1rewrite
from pycalver import version as v1version
from pycalver2 import rewrite as v2rewrite
from pycalver2 import version as v2version

# pylint:disable=protected-access ; allowed for test code


REWRITE_FIXTURE = """
# SPDX-License-Identifier: MIT
__version__ = "v201809.0002-beta"
"""


def test_rewrite_lines():
    old_lines = REWRITE_FIXTURE.splitlines()
    patterns  = ['__version__ = "{pycalver}"']
    new_vinfo = v1version.parse_version_info("v201911.0003")
    new_lines = v1rewrite.rewrite_lines(patterns, new_vinfo, old_lines)

    assert len(new_lines) == len(old_lines)
    assert "v201911.0003" not in "\n".join(old_lines)
    assert "v201911.0003" in "\n".join(new_lines)


def test_rewrite_final():
    # Patterns written with {release_tag} placeholder preserve
    # the release tag even if the new version is -final

    old_lines = REWRITE_FIXTURE.splitlines()
    patterns  = ['__version__ = "v{year}{month}.{build_no}-{release_tag}"']
    new_vinfo = v1version.parse_version_info("v201911.0003")
    new_lines = v1rewrite.rewrite_lines(patterns, new_vinfo, old_lines)

    assert len(new_lines) == len(old_lines)
    assert "v201911.0003" not in "\n".join(old_lines)
    assert "None" not in "\n".join(new_lines)
    assert "v201911.0003-final" in "\n".join(new_lines)


def test_iter_file_paths():
    with util.Project(project="a") as project:
        ctx = config.init_project_ctx(project.dir)
        cfg = config.parse(ctx)
        assert cfg

        _paths_and_patterns = v1rewrite.iter_file_paths(cfg.file_patterns)
        file_paths          = {str(file_path) for file_path, patterns in _paths_and_patterns}

    assert file_paths == {"pycalver.toml", "README.md"}


def test_iter_file_globs():
    with util.Project(project="b") as project:
        ctx = config.init_project_ctx(project.dir)
        cfg = config.parse(ctx)
        assert cfg

        _paths_and_patterns = v1rewrite.iter_file_paths(cfg.file_patterns)
        file_paths          = {str(file_path) for file_path, patterns in _paths_and_patterns}

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
            list(v1rewrite.iter_file_paths(cfg.file_patterns))
            assert False, "expected IOError"
        except IOError as ex:
            assert "setup.py" in str(ex)


def test_error_bad_pattern():
    with util.Project(project="b") as project:
        ctx = config.init_project_ctx(project.dir)
        cfg = config.parse(ctx)
        assert cfg

        patterns = copy.deepcopy(cfg.file_patterns)
        patterns["setup.py"] = patterns["setup.py"][0] + "invalid"

        try:
            new_vinfo = v1version.parse_version_info("v201809.1234")
            list(v1rewrite.diff(new_vinfo, patterns))
            assert False, "expected v1rewrite.NoPatternMatch"
        except v1rewrite.NoPatternMatch as ex:
            assert "setup.py" in str(ex)


OPTIONAL_RELEASE_FIXTURE = """
# SPDX-License-Identifier: BSD
__version__ = "2018.0002-beta"
"""


def test_v1_optional_release():
    old_lines = OPTIONAL_RELEASE_FIXTURE.splitlines()
    pattern   = "{year}.{build_no}{release}"
    patterns  = ['__version__ = "{year}.{build_no}{release}"']

    new_vinfo = v1version.parse_version_info("2019.0003", pattern)
    new_lines = v1rewrite.rewrite_lines(patterns, new_vinfo, old_lines)

    assert len(new_lines) == len(old_lines)
    assert "2019.0003" not in "\n".join(old_lines)
    new_text = "\n".join(new_lines)
    assert "2019.0003" in new_text

    new_vinfo = v1version.parse_version_info("2019.0004-beta", pattern)
    new_lines = v1rewrite.rewrite_lines(patterns, new_vinfo, old_lines)

    # make sure optional release tag is added back on
    assert len(new_lines) == len(old_lines)
    assert "2019.0004-beta" not in "\n".join(old_lines)
    assert "2019.0004-beta" in "\n".join(new_lines)


def test_v2_optional_release():
    old_lines = OPTIONAL_RELEASE_FIXTURE.splitlines()
    pattern   = "YYYY.BUILD[-TAG]"
    patterns  = ['__version__ = "YYYY.BUILD[-TAG]"']

    new_vinfo = v2version.parse_version_info("2019.0003", pattern)
    new_lines = v2rewrite.rewrite_lines(patterns, new_vinfo, old_lines)

    assert len(new_lines) == len(old_lines)
    assert "2019.0003" not in "\n".join(old_lines)
    new_text = "\n".join(new_lines)
    assert "2019.0003" in new_text
    assert '__version__ = "2019.0003"' in new_text

    new_vinfo = v2version.parse_version_info("2019.0004-beta", pattern)
    new_lines = v2rewrite.rewrite_lines(patterns, new_vinfo, old_lines)

    # make sure optional release tag is added back on
    assert len(new_lines) == len(old_lines)
    assert "2019.0004-beta" not in "\n".join(old_lines)
    assert "2019.0004-beta" in "\n".join(new_lines)
