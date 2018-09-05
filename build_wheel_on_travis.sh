#!/bin/bash
if [ $(which python3.7) ]; then
    python3.7 --version
else
    curl -sSf -o python-3.7.tar.bz2 https://s3.amazonaws.com/travis-python-archives/binaries/ubuntu/16.04/x86_64/python-3.7.tar.bz2
    tar xjf python-3.7.tar.bz2 --directory /
    source $HOME/virtualenv/python3.7.0/bin/activate
fi

python3.7 --version
python3.7 -m pip install lib3to6
python3.7 setup.py bdist_wheel --python-tag=py2.py3
