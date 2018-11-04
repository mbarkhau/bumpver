# This file is part of the pycalver project
# https://gitlab.com/mbarkhau/pycalver
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT

import os
import sys
import setuptools


def project_path(*sub_paths):
    project_dirpath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(project_dirpath, *sub_paths)


def read(*sub_paths):
    with open(project_path(*sub_paths), mode="rb") as fh:
        return fh.read().decode("utf-8")


packages = setuptools.find_packages(project_path("src"))
package_dir = {"": "src"}


if any(arg.startswith("bdist") for arg in sys.argv):
    import lib3to6
    package_dir = lib3to6.fix(package_dir)


long_description = (
    read("README.rst") +
    "\n\n" +
    read("CHANGELOG.rst")
)


setuptools.setup(
    name="pycalver",
    license="MIT",
    author="Manuel Barkhau",
    author_email="@mbarkhau",
    url="https://gitlab.com/mbarkhau/pycalver",
    version="201809.2b0",

    keywords="version versioning bumpversion calver",
    description="CalVer versioning for python libraries.",
    long_description=long_description,

    packages=packages,
    package_dir=package_dir,
    zip_safe=True,
    install_requires=["typing", "click"],
    setup_requires=[
        "lib3to6==v201809.0017-alpha",
        "pytest-runner",
    ],
    tests_require=[
        "pytest",
    ],
    entry_points='''
        [console_scripts]
        pycalver=pycalver.__main__:cli
    ''',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
