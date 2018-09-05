#!/bin/bash
set -e
set -v

rst2html5 --strict README.rst > /dev/null
rst2html5 --strict CHANGELOG.rst > /dev/null

# first test module from installed wheel
python -m pip install $(ls -1t dist/pycalver*.whl | head -n 1)
grep 'coding: utf-8' $(python -c 'import pycalver;print(pycalver.__file__)')
python -m pytest --cov=pycalver test/

if [[ $(python -c "import sys;print(sys.version[:3])") == "3.7" ]]; then
  python -m flake8 src/pycalver/

  MYPYPATH=stubs/ python -m mypy src/pycalver/;

  # next test module from src/
  PYTHONPATH=src/:$PYTHONPATH python -m pytest --cov=pycalver test/;
fi

codecov
