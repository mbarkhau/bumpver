#!/bin/bash
set -e


if [[ $(python -c "import sys;sys.exit(sys.version[:3] < '3.6')")  ]]; then
    python --version
    python -m pip install setuptools lib3to6
    python setup.py bdist_wheel --python-tag=py2.py3
else
    curl -sSf -o python-3.6.tar.bz2 https://s3.amazonaws.com/travis-python-archives/binaries/ubuntu/16.04/x86_64/python-3.6.tar.bz2
    tar xjf python-3.6.tar.bz2 --directory /
    source $HOME/virtualenv/python3.6.0/bin/activate

    python3.6 --version
    python3.6 -m pip install setuptools lib3to6
    python3.6 setup.py bdist_wheel --python-tag=py2.py3
fi

