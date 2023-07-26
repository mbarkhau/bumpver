#!/usr/bin/env python
from os import environ

print("I'm a pre commit hook. The old version was: " + environ.get('BUMPVER_OLD_VERSION', ''))
