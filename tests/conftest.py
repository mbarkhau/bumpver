from __future__ import annotations

import os
import pathlib
import platform
import typing

import pytest


@pytest.fixture(scope="session", autouse=True)
def _cwd() -> typing.Generator[None, None, None]:
    """
    The tests assume that the working directory is at the root of this project.
    This fixture makes sure it is just that.
    """
    original_cwd = os.getcwd()

    try:
        root_path = pathlib.Path(__file__).resolve().absolute().parent.parent
        os.chdir(root_path)

        yield

    finally:
        os.chdir(original_cwd)


@pytest.fixture(scope="session", autouse=platform.system() == "Windows")
def _fix_rmtree() -> typing.Generator[None, None, None]:
    """
    Fix some permission whine on Windows
    """
    import shutil
    import functools

    original_rmtree = shutil.rmtree

    def onerror(func, path, exc_info):
        """
        Error handler for ``shutil.rmtree``.

        If the error is due to an access error (read only file)
        it attempts to add write permission and then retries.

        If the error is for another reason it re-raises the error.

        Usage : ``shutil.rmtree(path, onerror=onerror)``
        """
        import stat

        # Is the error an access error?
        if not os.access(path, os.W_OK):
            os.chmod(path, stat.S_IWUSR)
            func(path)
        else:
            raise

    try:
        shutil.rmtree = functools.partial(original_rmtree, onerror=onerror)

        yield

    finally:
        shutil.rmtree = original_rmtree
