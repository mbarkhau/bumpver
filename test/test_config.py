import io

from pycalver import config

from . import util


PYCALVER_TOML_FIXTURE_1 = """
[pycalver]
current_version = "v201808.0123-alpha"
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

[pycalver.file_patterns]
"README.md" = [
    "{version}",
    "{pep440_version}",
]
"pycalver.toml" = [
    'current_version = "{version}"',
]
"""


SETUP_CFG_FIXTURE = """
[pycalver]
current_version = "v201808.0456-beta"
commit = True
tag = True
push = True

[pycalver:file_patterns]
setup.py =
    {version}
    {pep440_version}
setup.cfg =
    current_version = "{version}"
"""


def mk_buf(text):
    buf = io.StringIO()
    buf.write(text)
    buf.seek(0)
    return buf


def test_parse_toml_1():
    buf = mk_buf(PYCALVER_TOML_FIXTURE_1)

    raw_cfg = config._parse_toml(buf)
    cfg     = config._parse_config(raw_cfg)

    assert cfg.current_version == "v201808.0123-alpha"
    assert cfg.version_pattern == "{pycalver}"
    assert cfg.commit is True
    assert cfg.tag    is True
    assert cfg.push   is True

    assert "pycalver.toml" in cfg.file_patterns
    assert cfg.file_patterns["README.md"    ] == ["{pycalver}", "{pep440_pycalver}"]
    assert cfg.file_patterns["pycalver.toml"] == ['current_version = "{pycalver}"']


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
    assert cfg.file_patterns["README.md"    ] == ["{semver}", "{semver}"]
    assert cfg.file_patterns["pycalver.toml"] == ['current_version = "{semver}"']


def test_parse_cfg():
    buf = mk_buf(SETUP_CFG_FIXTURE)

    raw_cfg = config._parse_cfg(buf)
    cfg     = config._parse_config(raw_cfg)

    assert cfg.current_version == "v201808.0456-beta"
    assert cfg.commit is True
    assert cfg.tag    is True
    assert cfg.push   is True

    assert "setup.cfg" in cfg.file_patterns
    assert cfg.file_patterns["setup.py" ] == ["{pycalver}", "{pep440_pycalver}"]
    assert cfg.file_patterns["setup.cfg"] == ['current_version = "{pycalver}"']


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
    project_path = util.FIXTURES_DIR / "project_a"
    config_path  = util.FIXTURES_DIR / "project_a" / "pycalver.toml"

    with config_path.open() as fh:
        config_data = fh.read()

    assert "v201710.0123-alpha" in config_data

    ctx = config.init_project_ctx(project_path)
    assert ctx == config.ProjectContext(project_path, config_path, "toml", None)

    cfg = config.parse(ctx)

    assert cfg

    assert cfg.current_version == "v201710.0123-alpha"
    assert cfg.commit is True
    assert cfg.tag    is True
    assert cfg.push   is True

    assert set(cfg.file_patterns.keys()) == {"pycalver.toml", "README.md"}


def test_parse_project_cfg():
    project_path = util.FIXTURES_DIR / "project_b"
    config_path  = util.FIXTURES_DIR / "project_b" / "setup.cfg"

    with config_path.open() as fh:
        config_data = fh.read()

    assert "v201307.0456-beta" in config_data

    ctx = config.init_project_ctx(project_path)
    assert ctx == config.ProjectContext(project_path, config_path, 'cfg', None)

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
    setup_cfg    = project_path.join("pycalver.toml")
    setup_cfg.write(PYCALVER_TOML_FIXTURE_1)

    ctx = config.init_project_ctx(project_path)
    assert ctx == config.ProjectContext(project_path, setup_cfg, 'toml', None)

    cfg = config.parse(ctx)

    assert cfg
    assert cfg.current_version == "v201808.0123-alpha"
    assert cfg.tag    is True
    assert cfg.commit is True
    assert cfg.push   is True

    assert cfg.file_patterns == {
        "README.md"    : ["{pycalver}", "{pep440_pycalver}"],
        "pycalver.toml": ['current_version = "{pycalver}"'],
    }


def test_parse_cfg_file(tmpdir):
    project_path = tmpdir.mkdir("minimal")
    setup_cfg    = project_path.join("setup.cfg")
    setup_cfg.write(SETUP_CFG_FIXTURE)

    ctx = config.init_project_ctx(project_path)
    assert ctx == config.ProjectContext(project_path, setup_cfg, 'cfg', None)

    cfg = config.parse(ctx)

    assert cfg
    assert cfg.current_version == "v201808.0456-beta"
    assert cfg.tag    is True
    assert cfg.commit is True
    assert cfg.push   is True

    assert cfg.file_patterns == {
        "setup.py" : ["{pycalver}", "{pep440_pycalver}"],
        "setup.cfg": ['current_version = "{pycalver}"'],
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
                "[pycalver]",
                # f"current_version = v201808.0001-dev",
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
    setup_path.write("\n".join(("[pycalver]", "current_version = 0.1.0", "commit = False")))

    ctx = config.init_project_ctx(setup_path)
    assert ctx

    cfg = config.parse(ctx)
    assert cfg is None
