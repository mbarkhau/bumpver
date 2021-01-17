# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import re
import copy
from test import util

from bumpver import config
from bumpver import rewrite
from bumpver import v1rewrite
from bumpver import v1version
from bumpver import v2rewrite
from bumpver import v2version
from bumpver import v1patterns
from bumpver import v2patterns

# pylint:disable=protected-access ; allowed for test code


# Fix for Python<3.7
# https://stackoverflow.com/a/56935186/62997
copy._deepcopy_dispatch[type(re.compile(''))] = lambda r, _: r


REWRITE_FIXTURE = """
# SPDX-License-Identifier: MIT
__version__ = "v201809.0002-beta"
"""


def test_v1_rewrite_lines_basic():
    pattern   = v1patterns.compile_pattern("{pycalver}", '__version__ = "{pycalver}"')
    new_vinfo = v1version.parse_version_info("v201911.0003")

    old_lines = REWRITE_FIXTURE.splitlines()
    new_lines = v1rewrite.rewrite_lines([pattern], new_vinfo, old_lines)

    assert len(new_lines) == len(old_lines)
    assert "v201911.0003" not in "\n".join(old_lines)
    assert "v201911.0003" in "\n".join(new_lines)


def test_v1_rewrite_lines():
    version_pattern = "{pycalver}"
    new_vinfo       = v1version.parse_version_info("v201811.0123-beta", version_pattern)
    patterns        = [v1patterns.compile_pattern(version_pattern, '__version__ = "{pycalver}"')]
    lines           = v1rewrite.rewrite_lines(patterns, new_vinfo, ['__version__ = "v201809.0002-beta"'])
    assert lines == ['__version__ = "v201811.0123-beta"']

    patterns = [v1patterns.compile_pattern(version_pattern, '__version__ = "{pep440_version}"')]
    lines    = v1rewrite.rewrite_lines(patterns, new_vinfo, ['__version__ = "201809.2b0"'])
    assert lines == ['__version__ = "201811.123b0"']


def test_v2_rewrite_lines():
    version_pattern = "vYYYY0M.BUILD[-TAG]"
    new_vinfo       = v2version.parse_version_info("v201811.0123-beta", version_pattern)
    patterns        = [v2patterns.compile_pattern(version_pattern, '__version__ = "{version}"')]
    lines           = v2rewrite.rewrite_lines(patterns, new_vinfo, ['__version__ = "v201809.0002-alpha"   '])
    assert lines == ['__version__ = "v201811.0123-beta"   ']

    lines = v2rewrite.rewrite_lines(
        patterns, new_vinfo, ['__version__ = "v201809.0002-alpha"    # comment']
    )
    assert lines == ['__version__ = "v201811.0123-beta"    # comment']

    patterns  = [v2patterns.compile_pattern(version_pattern, '__version__ = "YYYY0M.BLD[PYTAGNUM]"')]
    old_lines = ['__version__ = "201809.2a0"']
    lines     = v2rewrite.rewrite_lines(patterns, new_vinfo, old_lines)
    assert lines == ['__version__ = "201811.123b0"']


def test_v1_rewrite_final():
    # Patterns written with {release_tag} placeholder preserve
    # the release tag even if the new version is -final

    pattern = v1patterns.compile_pattern(
        "v{year}{month}.{build_no}-{release_tag}",
        '__version__ = "v{year}{month}.{build_no}-{release_tag}"',
    )
    new_vinfo = v1version.parse_version_info("v201911.0003")

    old_lines = REWRITE_FIXTURE.splitlines()
    new_lines = v1rewrite.rewrite_lines([pattern], new_vinfo, old_lines)

    assert len(new_lines) == len(old_lines)
    assert "v201911.0003" not in "\n".join(old_lines)
    assert "None" not in "\n".join(new_lines)
    assert "v201911.0003-final" in "\n".join(new_lines)


def test_iter_file_paths():
    with util.Project(project="a") as project:
        ctx = config.init_project_ctx(project.dir)
        assert ctx
        cfg = config.parse(ctx)
        assert cfg

        _paths_and_patterns = rewrite.iter_path_patterns_items(cfg.file_patterns)
        file_paths          = {str(file_path) for file_path, patterns in _paths_and_patterns}

    assert file_paths == {"bumpver.toml", "README.md"}


def test_iter_file_globs():
    with util.Project(project="b") as project:
        ctx = config.init_project_ctx(project.dir)
        cfg = config.parse(ctx)
        assert cfg

        _paths_and_patterns = rewrite.iter_path_patterns_items(cfg.file_patterns)
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
            list(rewrite.iter_path_patterns_items(cfg.file_patterns))
            assert False, "expected IOError"
        except IOError as ex:
            assert "setup.py" in str(ex)


def test_v1_error_bad_pattern():
    with util.Project(project="b") as project:
        ctx = config.init_project_ctx(project.dir)
        cfg = config.parse(ctx)
        assert cfg

        patterns         = copy.deepcopy(cfg.file_patterns)
        original_pattern = patterns["setup.py"][0]
        invalid_pattern  = v1patterns.compile_pattern(
            original_pattern.version_pattern,
            original_pattern.raw_pattern + ".invalid",
        )
        patterns["setup.py"] = [invalid_pattern]

        try:
            old_vinfo = v1version.parse_version_info("v201808.0233")
            new_vinfo = v1version.parse_version_info("v201809.1234")
            list(v1rewrite.diff(old_vinfo, new_vinfo, patterns))
            assert False, "expected rewrite.NoPatternMatch"
        except rewrite.NoPatternMatch as ex:
            assert "setup.py" in str(ex)


OPTIONAL_RELEASE_FIXTURE = """
# SPDX-License-Identifier: BSD
__version__ = "2018.0002-beta"
"""


def test_v1_optional_release():
    version_pattern = "{year}.{build_no}{release}"
    new_vinfo       = v1version.parse_version_info("2019.0003", version_pattern)

    raw_pattern = '__version__ = "{year}.{build_no}{release}"'
    pattern     = v1patterns.compile_pattern(version_pattern, raw_pattern)

    old_lines = OPTIONAL_RELEASE_FIXTURE.splitlines()
    new_lines = v1rewrite.rewrite_lines([pattern], new_vinfo, old_lines)

    assert len(new_lines) == len(old_lines)
    assert "2019.0003" not in "\n".join(old_lines)
    assert "2019.0003" in "\n".join(new_lines)
    assert '__version__ = "2019.0003"' in "\n".join(new_lines)

    new_vinfo = v1version.parse_version_info("2019.0004-beta", version_pattern)
    new_lines = v1rewrite.rewrite_lines([pattern], new_vinfo, old_lines)

    # make sure optional release tag is added back on
    assert len(new_lines) == len(old_lines)
    assert "2019.0004-beta" not in "\n".join(old_lines)
    assert "2019.0004-beta" in "\n".join(new_lines)
    assert '__version__ = "2019.0004-beta"' in "\n".join(new_lines)


def test_v2_optional_release():
    version_pattern = "YYYY.BUILD[-TAG]"
    new_vinfo       = v2version.parse_version_info("2019.0003", version_pattern)

    raw_pattern = '__version__ = "YYYY.BUILD[-TAG]"'
    pattern     = v2patterns.compile_pattern(version_pattern, raw_pattern)

    old_lines = OPTIONAL_RELEASE_FIXTURE.splitlines()
    new_lines = v2rewrite.rewrite_lines([pattern], new_vinfo, old_lines)

    assert len(new_lines) == len(old_lines)
    assert "2019.0003" not in "\n".join(old_lines)
    assert "2019.0003" in "\n".join(new_lines)
    assert '__version__ = "2019.0003"' in "\n".join(new_lines)

    new_vinfo = v2version.parse_version_info("2019.0004-beta", version_pattern)
    new_lines = v2rewrite.rewrite_lines([pattern], new_vinfo, old_lines)

    # make sure optional release tag is added back on
    assert len(new_lines) == len(old_lines)
    assert "2019.0004-beta" not in "\n".join(old_lines)
    assert "2019.0004-beta" in "\n".join(new_lines)
    assert '__version__ = "2019.0004-beta"' in "\n".join(new_lines)


def test_v1_iter_rewritten():
    version_pattern = "{year}{build}{release}"
    new_vinfo       = v1version.parse_version_info("2018.0123", version_pattern)

    init_pattern = v1patterns.compile_pattern(
        version_pattern, '__version__ = "{year}{build}{release}"'
    )
    file_patterns   = {"src/bumpver/__init__.py": [init_pattern]}
    rewritten_datas = v1rewrite.iter_rewritten(file_patterns, new_vinfo)
    rfd             = list(rewritten_datas)[0]
    expected        = [
        "# This file is part of the bumpver project",
        "# https://github.com/mbarkhau/bumpver",
        "#",
        "# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License",
        "# SPDX-License-Identifier: MIT",
        '"""BumpVer: A CLI program for versioning."""',
        '',
        '__version__ = "2018.0123"',
        '',
    ]
    assert rfd.new_lines == expected


def test_v2_iter_rewritten():
    version_pattern = "YYYY.BUILD[-TAG]"
    new_vinfo       = v2version.parse_version_info("2018.0123", version_pattern)

    file_patterns = {
        "src/bumpver/__init__.py": [
            v2patterns.compile_pattern(version_pattern, '__version__ = "YYYY.BUILD[-TAG]"'),
        ]
    }

    rewritten_datas = v2rewrite.iter_rewritten(file_patterns, new_vinfo)
    rfd             = list(rewritten_datas)[0]
    expected        = [
        "# This file is part of the bumpver project",
        "# https://github.com/mbarkhau/bumpver",
        "#",
        "# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License",
        "# SPDX-License-Identifier: MIT",
        '"""BumpVer: A CLI program for versioning."""',
        '',
        '__version__ = "2018.0123"',
        '',
    ]
    assert rfd.new_lines == expected


def test_v1_diff():
    version_pattern = "{year}{build}{release}"
    raw_pattern     = '__version__ = "{year}{build}{release}"'
    pattern         = v1patterns.compile_pattern(version_pattern, raw_pattern)
    file_patterns   = {"src/bumpver/__init__.py": [pattern]}

    old_vinfo = v1version.parse_version_info("v201809.0123")
    new_vinfo = v1version.parse_version_info("v201911.1124")
    assert new_vinfo > old_vinfo

    old_vinfo = v1version.parse_version_info("2018.0123", version_pattern)
    new_vinfo = v1version.parse_version_info("2019.1124", version_pattern)

    diff_str = v1rewrite.diff(old_vinfo, new_vinfo, file_patterns)
    lines    = diff_str.split("\n")

    assert lines[:2] == [
        "--- src/bumpver/__init__.py",
        "+++ src/bumpver/__init__.py",
    ]

    assert lines[6].startswith('-__version__ = "20')
    assert lines[7].startswith('+__version__ = "20')

    assert not lines[6].startswith('-__version__ = "2018.0123"')

    assert lines[7] == '+__version__ = "2019.1124"'

    raw_pattern   = "Copyright (c) 2018-{year}"
    pattern       = v1patterns.compile_pattern(version_pattern, raw_pattern)
    file_patterns = {'LICENSE': [pattern]}
    diff_str      = v1rewrite.diff(old_vinfo, new_vinfo, file_patterns)

    lines = diff_str.split("\n")
    assert lines[3].startswith("-MIT License Copyright (c) 2018-20")
    assert lines[4].startswith("+MIT License Copyright (c) 2018-2019")


def test_v2_diff():
    version_pattern = "YYYY.BUILD[-TAG]"
    raw_pattern     = '__version__ = "YYYY.BUILD[-TAG]"'
    pattern         = v2patterns.compile_pattern(version_pattern, raw_pattern)
    file_patterns   = {"src/bumpver/__init__.py": [pattern]}

    old_vinfo = v2version.parse_version_info("2018.0123", version_pattern)
    new_vinfo = v2version.parse_version_info("2019.1124", version_pattern)

    diff_str = v2rewrite.diff(old_vinfo, new_vinfo, file_patterns)
    lines    = diff_str.split("\n")

    assert lines[:2] == [
        "--- src/bumpver/__init__.py",
        "+++ src/bumpver/__init__.py",
    ]

    assert lines[6].startswith('-__version__ = "20')
    assert lines[7].startswith('+__version__ = "20')

    assert not lines[6].startswith('-__version__ = "2018.0123"')

    assert lines[7] == '+__version__ = "2019.1124"'

    raw_pattern   = "Copyright (c) 2018-YYYY"
    pattern       = v2patterns.compile_pattern(version_pattern, raw_pattern)
    file_patterns = {'LICENSE': [pattern]}
    diff_str      = v2rewrite.diff(old_vinfo, new_vinfo, file_patterns)

    lines = diff_str.split("\n")
    assert lines[3].startswith("-MIT License Copyright (c) 2018-20")
    assert lines[4].startswith("+MIT License Copyright (c) 2018-2019")
