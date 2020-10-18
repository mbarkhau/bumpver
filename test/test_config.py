# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import io
from test import util

from bumpver import config

# pylint:disable=redefined-outer-name ; pytest fixtures
# pylint:disable=protected-access ; allowed for test code


PYCALVER_TOML_FIXTURE_1 = """
[pycalver]
current_version = "v2020.1003-alpha"
version_pattern = "vYYYY.BUILD[-TAG]"
commit = true
tag = true
push = true

[pycalver.file_patterns]
"README.md" = [
    "{version}",
    "{pep440_version}",
]
"pycalver.toml" = [
    'current_version = "{version}"',
]
"""


PYCALVER_TOML_FIXTURE_2 = """
[pycalver]
current_version = "1.2.3"
version_pattern = "{semver}"
commit = false
tag = false
push = false

[pycalver.file_patterns]
"README.md" = [
    "{version}",
    "{pep440_version}",
]
"pycalver.toml" = [
    'current_version = "{version}"',
]
"""

CALVER_TOML_FIXTURE_3 = """
[bumpver]
current_version = "v201808.0123-alpha"
version_pattern = "vYYYY0M.BUILD[-TAG]"
commit = true
tag = true
push = true

[bumpver.file_patterns]
"README.md" = [
    "{version}",
    "{pep440_version}",
]
"bumpver.toml" = [
    'current_version = "{version}"',
]
"""


SETUP_CFG_FIXTURE = """
[bumpver]
current_version = "v201808.0456-beta"
version_pattern = "vYYYY0M.BUILD[-TAG]"
commit = True
tag = True
push = True

[bumpver:file_patterns]
setup.py =
    {version}
    {pep440_version}
setup.cfg =
    current_version = "{version}"
"""


NEW_PATTERN_CFG_FIXTURE = """
[bumpver]
current_version = "v201808.1456-beta"
version_pattern = "vYYYY0M.BUILD[-TAG]"
commit_message = "bump version to {new_version}"
commit = True
tag = True
push = True

[bumpver:file_patterns]
setup.py =
    {version}
    {pep440_version}
setup.cfg =
    current_version = "{version}"
src/project/*.py =
    Copyright (c) 2018-YYYY
"""


def mk_buf(text):
    buf = io.StringIO()
    buf.write(text)
    buf.seek(0)
    return buf


def _parse_raw_patterns_by_filepath(cfg):
    return {
        filepath: [pattern.raw_pattern for pattern in patterns]
        for filepath, patterns in cfg.file_patterns.items()
    }


def test_parse_toml_1():
    buf = mk_buf(PYCALVER_TOML_FIXTURE_1)

    raw_cfg = config._parse_toml(buf)
    cfg     = config._parse_config(raw_cfg)

    assert cfg.current_version == "v2020.1003-alpha"
    assert cfg.version_pattern == "vYYYY.BUILD[-TAG]"
    assert cfg.commit is True
    assert cfg.tag    is True
    assert cfg.push   is True

    files = set(cfg.file_patterns)
    assert "pycalver.toml" in files

    raw_patterns_by_path = _parse_raw_patterns_by_filepath(cfg)
    assert raw_patterns_by_path["README.md"    ] == ["vYYYY.BUILD[-TAG]", "YYYY.BLD[PYTAGNUM]"]
    assert raw_patterns_by_path["pycalver.toml"] == ['current_version = "vYYYY.BUILD[-TAG]"']


def test_parse_toml_2():
    buf = mk_buf(PYCALVER_TOML_FIXTURE_2)

    raw_cfg = config._parse_toml(buf)
    cfg     = config._parse_config(raw_cfg)

    assert cfg.current_version == "1.2.3"
    assert cfg.version_pattern == "{semver}"
    assert cfg.commit is False
    assert cfg.tag    is False
    assert cfg.push   is False

    assert "pycalver.toml" in cfg.file_patterns

    raw_patterns_by_path = _parse_raw_patterns_by_filepath(cfg)
    assert raw_patterns_by_path["README.md"    ] == ["{semver}", "{semver}"]
    assert raw_patterns_by_path["pycalver.toml"] == ['current_version = "{semver}"']


def test_parse_toml_3():
    buf = mk_buf(CALVER_TOML_FIXTURE_3)

    raw_cfg = config._parse_toml(buf)
    cfg     = config._parse_config(raw_cfg)

    assert cfg.current_version == "v201808.0123-alpha"
    assert cfg.version_pattern == "vYYYY0M.BUILD[-TAG]"
    assert cfg.commit is True
    assert cfg.tag    is True
    assert cfg.push   is True

    files = set(cfg.file_patterns)
    assert "bumpver.toml" in files

    raw_patterns_by_path = _parse_raw_patterns_by_filepath(cfg)
    assert raw_patterns_by_path["README.md"   ] == ["vYYYY0M.BUILD[-TAG]", "YYYY0M.BLD[PYTAGNUM]"]
    assert raw_patterns_by_path["bumpver.toml"] == ['current_version = "vYYYY0M.BUILD[-TAG]"']


def test_parse_v1_cfg():
    buf = mk_buf(SETUP_CFG_FIXTURE)

    raw_cfg = config._parse_cfg(buf)
    cfg     = config._parse_config(raw_cfg)

    assert cfg.current_version == "v201808.0456-beta"
    assert cfg.commit is True
    assert cfg.tag    is True
    assert cfg.push   is True

    files = set(cfg.file_patterns)
    assert "setup.cfg" in files

    raw_patterns_by_path = _parse_raw_patterns_by_filepath(cfg)
    assert raw_patterns_by_path["setup.py" ] == ["vYYYY0M.BUILD[-TAG]", "YYYY0M.BLD[PYTAGNUM]"]
    assert raw_patterns_by_path["setup.cfg"] == ['current_version = "vYYYY0M.BUILD[-TAG]"']


def test_parse_v2_cfg():
    buf = mk_buf(NEW_PATTERN_CFG_FIXTURE)

    raw_cfg = config._parse_cfg(buf)
    cfg     = config._parse_config(raw_cfg)
    assert cfg.current_version == "v201808.1456-beta"
    assert cfg.commit_message  == "bump version to {new_version}"
    assert cfg.commit is True
    assert cfg.tag    is True
    assert cfg.push   is True

    files = set(cfg.file_patterns)
    assert "setup.py" in files
    assert "setup.cfg" in files

    raw_patterns_by_path = _parse_raw_patterns_by_filepath(cfg)
    assert raw_patterns_by_path["setup.py"] == ["vYYYY0M.BUILD[-TAG]", "YYYY0M.BLD[PYTAGNUM]"]
    assert raw_patterns_by_path["setup.cfg"] == ['current_version = "vYYYY0M.BUILD[-TAG]"']
    assert raw_patterns_by_path["src/project/*.py"] == ["Copyright (c) 2018-YYYY"]


def test_parse_default_toml():
    project_path = util.FIXTURES_DIR / "project_a"

    ctx          = config.init_project_ctx(project_path)
    default_toml = config.default_config(ctx)

    buf     = mk_buf(default_toml)
    raw_cfg = config._parse_toml(buf)
    cfg     = config._parse_config(raw_cfg)

    assert cfg


def test_parse_default_cfg():
    project_path = util.FIXTURES_DIR / "project_b"

    ctx         = config.init_project_ctx(project_path)
    default_cfg = config.default_config(ctx)

    buf     = mk_buf(default_cfg)
    raw_cfg = config._parse_cfg(buf)
    cfg     = config._parse_config(raw_cfg)

    assert cfg


def test_parse_project_toml():
    project_path    = util.FIXTURES_DIR / "project_a"
    config_path     = util.FIXTURES_DIR / "project_a" / "bumpver.toml"
    config_rel_path = "bumpver.toml"

    with config_path.open() as fobj:
        config_data = fobj.read()

    assert "v2017.0123-alpha" in config_data

    ctx = config.init_project_ctx(project_path)
    assert ctx == config.ProjectContext(project_path, config_path, config_rel_path, "toml", None)

    cfg = config.parse(ctx)

    assert cfg

    assert cfg.current_version == "v2017.0123-alpha"
    assert cfg.commit is True
    assert cfg.tag    is True
    assert cfg.push   is True

    files = set(cfg.file_patterns.keys())
    assert files == {"bumpver.toml", "README.md"}


def test_parse_project_cfg():
    project_path    = util.FIXTURES_DIR / "project_b"
    config_path     = util.FIXTURES_DIR / "project_b" / "setup.cfg"
    config_rel_path = "setup.cfg"

    with config_path.open() as fobj:
        config_data = fobj.read()

    assert "v201307.0456-beta" in config_data

    ctx = config.init_project_ctx(project_path)
    assert ctx == config.ProjectContext(project_path, config_path, config_rel_path, 'cfg', None)

    cfg = config.parse(ctx)

    assert cfg
    assert cfg.current_version == "v201307.0456-beta"
    assert cfg.commit is True
    assert cfg.tag    is True
    assert cfg.push   is True

    assert set(cfg.file_patterns.keys()) == {
        "setup.py",
        "README.rst",
        "setup.cfg",
        "src/module_v*/__init__.py",
    }


def test_parse_toml_file(tmpdir):
    project_path = tmpdir.mkdir("minimal")
    cfg_file     = project_path.join("pycalver.toml")
    cfg_file.write(PYCALVER_TOML_FIXTURE_1)
    cfg_file_rel_path = "pycalver.toml"

    ctx = config.init_project_ctx(project_path)
    assert ctx == config.ProjectContext(project_path, cfg_file, cfg_file_rel_path, 'toml', None)

    cfg = config.parse(ctx)

    assert cfg
    assert cfg.current_version == "v2020.1003-alpha"
    assert cfg.version_pattern == "vYYYY.BUILD[-TAG]"
    assert cfg.tag    is True
    assert cfg.commit is True
    assert cfg.push   is True

    raw_patterns_by_filepath = _parse_raw_patterns_by_filepath(cfg)
    assert raw_patterns_by_filepath == {
        "README.md"    : ["vYYYY.BUILD[-TAG]", "YYYY.BLD[PYTAGNUM]"],
        "pycalver.toml": ['current_version = "vYYYY.BUILD[-TAG]"'],
    }


def test_parse_default_pattern():
    project_path    = util.FIXTURES_DIR / "project_c"
    config_path     = util.FIXTURES_DIR / "project_c" / "pyproject.toml"
    config_rel_path = "pyproject.toml"

    ctx = config.init_project_ctx(project_path)

    assert ctx == config.ProjectContext(project_path, config_path, config_rel_path, "toml", None)

    cfg = config.parse(ctx)

    assert cfg

    assert cfg.current_version == "v2017q1.54321"
    # assert cfg.version_pattern == "vYYYYqQ.BUILD"
    assert cfg.version_pattern == "v{year}q{quarter}.{build_no}"
    assert cfg.commit is True
    assert cfg.tag    is True
    assert cfg.push   is True

    raw_patterns_by_filepath = _parse_raw_patterns_by_filepath(cfg)
    assert raw_patterns_by_filepath == {
        "pyproject.toml": [r'current_version = "v{year}q{quarter}.{build_no}"']
    }


def test_parse_cfg_file(tmpdir):
    project_path = tmpdir.mkdir("minimal")
    setup_cfg    = project_path.join("setup.cfg")
    setup_cfg.write(SETUP_CFG_FIXTURE)
    setup_cfg_rel_path = "setup.cfg"

    ctx = config.init_project_ctx(project_path)
    assert ctx == config.ProjectContext(project_path, setup_cfg, setup_cfg_rel_path, 'cfg', None)

    cfg = config.parse(ctx)

    assert cfg
    assert cfg.current_version == "v201808.0456-beta"
    assert cfg.version_pattern == "vYYYY0M.BUILD[-TAG]"
    assert cfg.tag    is True
    assert cfg.commit is True
    assert cfg.push   is True

    raw_patterns_by_filepath = _parse_raw_patterns_by_filepath(cfg)
    assert raw_patterns_by_filepath == {
        "setup.py" : ["vYYYY0M.BUILD[-TAG]", "YYYY0M.BLD[PYTAGNUM]"],
        "setup.cfg": ['current_version = "vYYYY0M.BUILD[-TAG]"'],
    }


def test_parse_config_missing(tmpdir):
    ctx = config.init_project_ctx("does_not_exist/setup.cfg")
    assert ctx

    cfg = config.parse(ctx)
    assert cfg is None

    setup_path = tmpdir.mkdir("fail").join("setup.cfg")
    ctx        = config.init_project_ctx(setup_path)
    assert ctx

    cfg = config.parse(ctx)
    assert cfg is None


def test_parse_empty_config(tmpdir):
    setup_path = tmpdir.mkdir("fail").join("setup.cfg")
    setup_path.write("")
    ctx = config.init_project_ctx(setup_path)
    assert ctx

    cfg = config.parse(ctx)
    assert cfg is None


def test_parse_missing_version(tmpdir):
    setup_path = tmpdir.mkdir("fail").join("setup.cfg")
    setup_path.write(
        "\n".join(
            (
                "[bumpver]",
                # f"current_version = v201808.1001-dev",
                "commit = False",
            )
        )
    )

    ctx = config.init_project_ctx(setup_path)
    assert ctx

    cfg = config.parse(ctx)
    assert cfg is None


def test_parse_invalid_version(tmpdir):
    setup_path = tmpdir.mkdir("fail").join("setup.cfg")
    setup_path.write("\n".join(("[bumpver]", "current_version = 0.1.0", "commit = False")))

    ctx = config.init_project_ctx(setup_path)
    assert ctx

    cfg = config.parse(ctx)
    assert cfg is None
