"""Shared fixtures for integration tests."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from lcc.api.server import create_app
from lcc.auth.core import UserRole, get_password_hash
from lcc.auth.repository import UserRepository
from lcc.config import LCCConfig


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_config(temp_dir: Path) -> LCCConfig:
    """Create a test configuration."""
    # Set environment variables for test config
    os.environ["LCC_CACHE_DIR"] = str(temp_dir / "cache")
    os.environ["LCC_DB_PATH"] = str(temp_dir / "test.db")
    os.environ["LCC_POLICY_DIR"] = str(temp_dir / "policies")
    os.environ["LCC_LOG_LEVEL"] = "ERROR"  # Reduce log noise in tests

    # Create necessary directories
    (temp_dir / "cache").mkdir(parents=True, exist_ok=True)
    (temp_dir / "policies").mkdir(parents=True, exist_ok=True)

    # Load config with test settings
    config = LCCConfig()

    yield config

    # Cleanup environment variables
    for key in ["LCC_CACHE_DIR", "LCC_DB_PATH", "LCC_POLICY_DIR", "LCC_LOG_LEVEL"]:
        os.environ.pop(key, None)


@pytest.fixture
def test_app(test_config: LCCConfig) -> TestClient:
    """Create a test FastAPI application."""
    app = create_app(config_path=None)  # Will use env vars set by test_config
    client = TestClient(app)
    return client


@pytest.fixture
def user_repository(test_config: LCCConfig) -> UserRepository:
    """Create a user repository for testing."""
    return UserRepository(test_config.database_path)


@pytest.fixture
def test_admin_user(user_repository: UserRepository) -> dict:
    """Create a test admin user and return credentials."""
    username = "test_admin"
    password = "test_password_123"

    # Create admin user
    user = user_repository.create_user(
        username=username,
        password=password,
        email="admin@test.com",
        full_name="Test Admin",
        role=UserRole.ADMIN
    )

    return {
        "username": username,
        "password": password,
        "email": user.email,
        "role": user.role.value
    }


@pytest.fixture
def test_regular_user(user_repository: UserRepository) -> dict:
    """Create a test regular user and return credentials."""
    username = "test_user"
    password = "test_password_456"

    # Create regular user
    user = user_repository.create_user(
        username=username,
        password=password,
        email="user@test.com",
        full_name="Test User",
        role=UserRole.USER
    )

    return {
        "username": username,
        "password": password,
        "email": user.email,
        "role": user.role.value
    }


@pytest.fixture
def admin_token(test_app: TestClient, test_admin_user: dict) -> str:
    """Get an admin authentication token."""
    response = test_app.post(
        "/auth/login",
        data={
            "username": test_admin_user["username"],
            "password": test_admin_user["password"]
        }
    )
    assert response.status_code == 200, f"Failed to login: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def user_token(test_app: TestClient, test_regular_user: dict) -> str:
    """Get a regular user authentication token."""
    response = test_app.post(
        "/auth/login",
        data={
            "username": test_regular_user["username"],
            "password": test_regular_user["password"]
        }
    )
    assert response.status_code == 200, f"Failed to login: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def test_policy_data() -> dict:
    """Sample policy data for testing."""
    return {
        "name": "test-policy",
        "version": "1.0",
        "disclaimer": "Test policy for integration testing",
        "description": "A test policy",
        "default_context": "production",
        "contexts": {
            "production": {
                "allow": ["MIT", "Apache-2.0", "BSD-3-Clause"],
                "deny": ["GPL-*", "AGPL-*"],
                "review": ["LGPL-*"],
                "deny_reasons": {
                    "GPL-*": "Strong copyleft incompatible with proprietary software",
                    "AGPL-*": "Network copyleft requires source disclosure"
                },
                "dual_license_preference": "most_permissive"
            },
            "development": {
                "allow": ["*"],
                "deny": [],
                "review": []
            }
        }
    }


@pytest.fixture
def sample_project_dir(temp_dir: Path) -> Path:
    """Create a sample project directory with various license files."""
    project_dir = temp_dir / "sample_project"
    project_dir.mkdir(parents=True, exist_ok=True)

    # Create package.json with MIT license
    (project_dir / "package.json").write_text(
        '{"name": "test-project", "version": "1.0.0", "license": "MIT"}'
    )

    # Create requirements.txt
    (project_dir / "requirements.txt").write_text(
        "requests==2.31.0\n"
        "flask==3.0.0\n"
    )

    # Create a LICENSE file
    (project_dir / "LICENSE").write_text(
        "MIT License\n\n"
        "Copyright (c) 2024 Test Project\n\n"
        "Permission is hereby granted..."
    )

    return project_dir
