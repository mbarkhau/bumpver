import io

from pycalver import config


def test_parse_default_config():
    buf = io.StringIO()
    for line in config.default_config_lines():
        buf.write(line + "\n")

    buf.seek(0)
    cfg = config.parse_buffer(buf)

    assert cfg
    assert cfg.current_version.endswith(".0001-dev")
    assert cfg.tag
    assert cfg.commit

    assert "setup.py" in cfg.file_patterns
    assert "setup.cfg" in cfg.file_patterns
    assert "README.rst" in cfg.file_patterns


def test_parse(tmpdir):
    setup_path = tmpdir.mkdir("minimal").join("setup.cfg")
    setup_path.write("\n".join((
        "[pycalver]",
        f"current_version = v201808.0001-dev",
        "commit = False",
        "tag = False",
        "",
        "[pycalver:file:setup.cfg]",
        "patterns = ",
        "    current_version = {version}",
    )))

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
    setup_path.write("\n".join((
        "[pycalver]",
        # f"current_version = v201808.0001-dev",
        "commit = False",
    )))

    cfg = config.parse(str(setup_path))
    assert cfg is None


def test_parse_invalid_version(tmpdir):
    setup_path = tmpdir.mkdir("fail").join("setup.cfg")
    setup_path.write("\n".join((
        "[pycalver]",
        f"current_version = 0.1.0",
        "commit = False",
    )))

    cfg = config.parse(str(setup_path))
    assert cfg is None
