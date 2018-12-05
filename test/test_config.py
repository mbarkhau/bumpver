import io

from pycalver import config

from . import util as test_util


PYCALVER_TOML_FIXTURE = """
[pycalver]
current_version = "v201808.0123-dev"
commit = true
tag = true
push = true

[pycalver.file_patterns]
"setup.py" = [
    "{version}",
    "{pep440_version}",
]
"pycalver.toml" = [
    'current_version = "{version}"',
]
"""


SETUP_CFG_FIXTURE = """
[pycalver]
current_version = "v201808.0456-dev"
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


def test_parse_toml():
    buf = mk_buf(PYCALVER_TOML_FIXTURE)

    raw_cfg = config._parse_toml(buf)
    cfg     = config._parse_config(raw_cfg)

    assert cfg.current_version == "v201808.0123-dev"
    assert cfg.commit is True
    assert cfg.tag    is True
    assert cfg.push   is True

    assert "pycalver.toml" in cfg.file_patterns
    assert cfg.file_patterns["setup.py"     ] == ["{version}", "{pep440_version}"]
    assert cfg.file_patterns["pycalver.toml"] == ['current_version = "{version}"']


def test_parse_cfg():
    buf = mk_buf(SETUP_CFG_FIXTURE)

    raw_cfg = config._parse_cfg(buf)
    cfg     = config._parse_config(raw_cfg)

    assert cfg.current_version == "v201808.0456-dev"
    assert cfg.commit is True
    assert cfg.tag    is True
    assert cfg.push   is True

    assert "setup.cfg" in cfg.file_patterns
    assert cfg.file_patterns["setup.py" ] == ["{version}", "{pep440_version}"]
    assert cfg.file_patterns["setup.cfg"] == ['current_version = "{version}"']


def test_parse_default_toml():
    project_path = test_util.FIXTURES_DIR / "project_a"
    config_path  = test_util.FIXTURES_DIR / "project_a" / "pycalver.toml"

    ctx = config.ProjectContext(project_path, config_path, "toml", None)
    buf = mk_buf(config.default_config(ctx))

    raw_cfg = config._parse_toml(buf)
    cfg     = config._parse_config(raw_cfg)

    assert cfg
    assert cfg.current_version.endswith(".0001-dev")
    assert cfg.commit is True
    assert cfg.tag    is True
    assert cfg.push   is True

    assert "setup.py" in cfg.file_patterns
    assert "README.md" in cfg.file_patterns
    assert "pycalver.toml" in cfg.file_patterns


def test_parse_default_cfg():
    project_path = test_util.FIXTURES_DIR / "project_a"
    config_path  = test_util.FIXTURES_DIR / "project_a" / "setup.cfg"

    ctx = config.ProjectContext(project_path, config_path, "cfg", None)
    buf = mk_buf(config.default_config(ctx))

    raw_cfg = config._parse_cfg(buf)
    cfg     = config._parse_config(raw_cfg)

    assert cfg
    assert cfg.current_version.endswith(".0001-dev")
    assert cfg.commit is True
    assert cfg.tag    is True
    assert cfg.push   is True

    assert "setup.py" in cfg.file_patterns
    assert "README.md" in cfg.file_patterns
    assert "setup.cfg" in cfg.file_patterns


def test_parse_cfg_file(tmpdir):
    setup_path = tmpdir.mkdir("minimal").join("setup.cfg")
    setup_path.write(SETUP_CFG_FIXTURE)

    cfg = config.parse(str(setup_path))

    assert cfg
    assert cfg.current_version == "v201808.0001-dev"
    assert not cfg.tag
    assert not cfg.commit

    assert cfg.file_patterns == {"setup.cfg": ["current_version = {version}"]}


def test_parse_config_missing(tmpdir):
    cfg = config.parse("does_not_exist/setup.cfg")
    assert cfg is None

    setup_path = tmpdir.mkdir("fail").join("setup.cfg")

    cfg = config.parse(str(setup_path))
    assert cfg is None


def test_parse_empty_config(tmpdir):
    setup_path = tmpdir.mkdir("fail").join("setup.cfg")
    setup_path.write("")

    cfg = config.parse(str(setup_path))
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

    cfg = config.parse(str(setup_path))
    assert cfg is None


def test_parse_invalid_version(tmpdir):
    setup_path = tmpdir.mkdir("fail").join("setup.cfg")
    setup_path.write("\n".join(("[pycalver]", "current_version = 0.1.0", "commit = False")))

    cfg = config.parse(str(setup_path))
    assert cfg is None
