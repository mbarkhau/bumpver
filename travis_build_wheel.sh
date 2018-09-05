#!/bin/bash
set -e

if [[ $(which python3.6) ]]; then
    python3.6 --version
else
    curl -sSf -o python-3.6.tar.bz2 https://s3.amazonaws.com/travis-python-archives/binaries/ubuntu/16.04/x86_64/python-3.6.tar.bz2
    tar xjf python-3.6.tar.bz2 --directory /
    source $HOME/virtualenv/python3.6.0/bin/activate
fi

python3.6 --version
python3.6 -m pip install setuptools lib3to6
python3.6 setup.py bdist_wheel --python-tag=py2.py3
