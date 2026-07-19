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

"""Security tests for JWT type validation and initial-admin seeding."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from lcc.auth.core import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from lcc.auth.repository import UserRepository


@pytest.fixture(autouse=True)
def _secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LCC_SECRET_KEY", "unit-test-secret-key")


def test_access_token_accepted_as_access() -> None:
    token = create_access_token({"sub": "u", "role": "admin"})
    assert decode_token(token).username == "u"


def test_refresh_token_rejected_as_access() -> None:
    token = create_refresh_token({"sub": "u", "role": "admin"})
    with pytest.raises(HTTPException) as exc:
        decode_token(token)  # default expected_type="access"
    assert exc.value.status_code == 401


def test_refresh_token_accepted_with_refresh_type() -> None:
    token = create_refresh_token({"sub": "u", "role": "admin"})
    assert decode_token(token, expected_type="refresh").username == "u"


def test_access_token_rejected_as_refresh() -> None:
    token = create_access_token({"sub": "u", "role": "admin"})
    with pytest.raises(HTTPException):
        decode_token(token, expected_type="refresh")


def test_initial_admin_has_no_fixed_password(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("LCC_ADMIN_PASSWORD", raising=False)
    repo = UserRepository(tmp_path / "users.db")

    admin = repo.get_user("admin")
    assert admin is not None
    assert admin.must_change_password is True
    # The old hardcoded admin/admin credential must not work.
    assert not verify_password("admin", admin.hashed_password)


def test_initial_admin_uses_env_password(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LCC_ADMIN_PASSWORD", "s3cret-from-env")
    repo = UserRepository(tmp_path / "users.db")

    admin = repo.get_user("admin")
    assert admin is not None
    assert verify_password("s3cret-from-env", admin.hashed_password)
