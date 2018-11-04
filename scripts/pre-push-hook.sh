#!/bin/bash
set -euo pipefail;

make fmt;

git diff --exit-code --stat src/;
git diff --exit-code --stat test/;
git diff --exit-code --stat scripts/;
git diff --exit-code --stat requirements/;

make lint;
make test;
