from pycalver import rewrite


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
