#!/bin/bash
if [ $(which python3.7) ]; then
    echo "installed"
    exit 0
fi


echo $PAtH
echo "installing"
curl -sSf -o python-3.7.tar.bz2 https://s3.amazonaws.com/travis-python-archives/binaries/ubuntu/16.04/x86_64/python-3.7.tar.bz2
tar xjf python-3.7.tar.bz2 --verbose --directory /
ls -l /home/travis/virtualenv/
which python3.7
python --version

# ln -s /home/travis/virtualenv/python3.7.0/bin/python

