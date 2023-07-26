#!/usr/bin/env python
from os import environ

print("I'm a post commit hook. The new version is: " + environ.get('BUMPVER_NEW_VERSION', ''))
