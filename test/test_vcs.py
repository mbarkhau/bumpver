# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import pytest

from bumpver import vcs


class _FakeAPI:
    def __init__(self, branch):
        self.name   = 'git'
        self._branch = branch

    def current_branch(self):
        return self._branch


def test_assert_allowed_branch_empty_allows_anything():
    vcs.assert_allowed_branch(_FakeAPI('feature/xyz'), [])


def test_assert_allowed_branch_exact_match():
    vcs.assert_allowed_branch(_FakeAPI('master'), ['master', 'main'])


def test_assert_allowed_branch_glob_match():
    vcs.assert_allowed_branch(_FakeAPI('release-1.2'), ['master', 'release-*'])


def test_assert_allowed_branch_rejects_unmatched():
    with pytest.raises(SystemExit):
        vcs.assert_allowed_branch(_FakeAPI('feature/xyz'), ['master', 'main'])


def test_assert_allowed_branch_unknown_branch_is_skipped():
    vcs.assert_allowed_branch(_FakeAPI(None), ['master'])
