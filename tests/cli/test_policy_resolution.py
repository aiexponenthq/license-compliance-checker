# Copyright 2025 Ajay Pundhir
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A stale ambient active policy must not abort a scan (finding M5)."""

from __future__ import annotations

import pytest

from lcc.cli.main import _resolve_policy_definition
from lcc.policy.base import PolicyError, PolicyManager


class _Manager(PolicyManager):
    def __init__(self, active):
        self._active = active

    def active_policy(self):
        return self._active

    def load_policy(self, name):
        raise PolicyError(f"Policy '{name}' not found")


def test_missing_ambient_policy_degrades_gracefully():
    manager = _Manager(active="does-not-exist")
    data, name = _resolve_policy_definition(manager, supplied=None)
    assert data is None
    assert name is None


def test_explicit_missing_policy_still_raises():
    manager = _Manager(active=None)
    with pytest.raises(PolicyError):
        _resolve_policy_definition(manager, supplied="does-not-exist")


def test_no_active_policy_returns_none():
    manager = _Manager(active=None)
    assert _resolve_policy_definition(manager, supplied=None) == (None, None)
