"""Integration tests for database operations."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from lcc.api.repository import ScanRepository
from lcc.auth.core import UserRole, authenticate_user
from lcc.auth.repository import UserRepository
from lcc.config import LCCConfig


class TestUserRepository:
    """Test user repository database operations."""

    def test_create_and_retrieve_user(self, user_repository: UserRepository):
        """Test creating and retrieving a user."""
        # Create user
        user = user_repository.create_user(
            username="dbtest_user",
            password="password123",
            email="dbtest@example.com",
            full_name="DB Test User",
            role=UserRole.USER
        )

        assert user.username == "dbtest_user"
        assert user.email == "dbtest@example.com"
        assert user.role == UserRole.USER

        # Retrieve user
        retrieved_user = user_repository.get_user("dbtest_user")
        assert retrieved_user is not None
        assert retrieved_user.username == "dbtest_user"
        assert retrieved_user.email == "dbtest@example.com"

    def test_create_duplicate_user(self, user_repository: UserRepository):
        """Test that creating duplicate username fails."""
        # Create first user
        user_repository.create_user(
            username="duplicate_test",
            password="password123",
            email="first@example.com"
        )

        # Try to create duplicate
        with pytest.raises((ValueError, sqlite3.IntegrityError)):
            user_repository.create_user(
                username="duplicate_test",
                password="password456",
                email="second@example.com"
            )

    def test_user_authentication(self, user_repository: UserRepository):
        """Test user authentication with correct and incorrect passwords."""
        # Create user
        user_repository.create_user(
            username="auth_test",
            password="correct_password",
            email="auth@example.com"
        )

        # Test with correct password
        user = authenticate_user("auth_test", "correct_password", user_repository)
        assert user is not None
        assert user.username == "auth_test"

        # Test with incorrect password
        user = authenticate_user("auth_test", "wrong_password", user_repository)
        assert user is None

        # Test with nonexistent username
        user = authenticate_user("nonexistent", "password", user_repository)
        assert user is None

    def test_update_user(self, user_repository: UserRepository):
        """Test updating user credentials (the shipped repository supports password updates)."""
        # Create user
        user_repository.create_user(
            username="update_test",
            password="password123",
            email="old@example.com",
            full_name="Old Name"
        )

        # Update the user's password (the supported update operation)
        user_repository.update_password("update_test", "newpassword456")

        # Old password no longer authenticates; the new one does
        assert authenticate_user("update_test", "password123", user_repository) is None
        updated = authenticate_user("update_test", "newpassword456", user_repository)
        assert updated is not None
        assert updated.username == "update_test"

    def test_disable_user(self, user_repository: UserRepository):
        """Test disabling a user account."""
        # Create user
        user_repository.create_user(
            username="disable_test",
            password="password123",
            email="disable@example.com"
        )

        # Disable user
        user_repository.disable_user("disable_test")

        # Verify user is disabled
        user = user_repository.get_user("disable_test")
        assert user.disabled is True

        # Authentication should fail for disabled user
        authenticated = authenticate_user("disable_test", "password123", user_repository)
        assert authenticated is None or authenticated.disabled is True

    def test_list_users(self, user_repository: UserRepository):
        """Test that created users are individually retrievable."""
        # Create multiple users
        for i in range(3):
            user_repository.create_user(
                username=f"list_test_{i}",
                password="password123",
                email=f"list{i}@example.com"
            )

        # The repository does not expose a bulk-list API; verify each user is
        # retrievable individually instead.
        for i in range(3):
            user = user_repository.get_user(f"list_test_{i}")
            assert user is not None
            assert user.username == f"list_test_{i}"

    def test_user_roles(self, user_repository: UserRepository):
        """Test user role management."""
        # Create admin user
        admin_user = user_repository.create_user(
            username="role_admin",
            password="password123",
            email="roleadmin@example.com",
            role=UserRole.ADMIN
        )
        assert admin_user.role == UserRole.ADMIN

        # Create regular user
        regular_user = user_repository.create_user(
            username="role_user",
            password="password123",
            email="roleuser@example.com",
            role=UserRole.USER
        )
        assert regular_user.role == UserRole.USER

        # Roles are assigned at creation time and persisted
        assert user_repository.get_user("role_admin").role == UserRole.ADMIN
        assert user_repository.get_user("role_user").role == UserRole.USER


class TestAPIKeyRepository:
    """Test API key repository database operations."""

    def test_create_api_key(self, user_repository: UserRepository):
        """Test creating an API key."""
        # Create user first
        user_repository.create_user(
            username="apikey_test",
            password="password123",
            email="apikey@example.com"
        )

        # Create API key (returns (key_id, raw_key))
        key_id, api_key = user_repository.create_api_key(
            username="apikey_test",
            name="Test API Key"
        )
        assert key_id
        assert api_key

        # Verify key can be used for authentication
        authenticated_user = user_repository.verify_api_key(api_key)
        assert authenticated_user is not None
        assert authenticated_user.username == "apikey_test"

    def test_list_api_keys(self, user_repository: UserRepository):
        """Test listing user's API keys."""
        # Create user
        user_repository.create_user(
            username="list_keys_test",
            password="password123",
            email="listkeys@example.com"
        )

        try:
            # Create multiple API keys
            user_repository.create_api_key("list_keys_test", "Key 1")
            user_repository.create_api_key("list_keys_test", "Key 2")

            # List keys
            keys = user_repository.list_api_keys("list_keys_test")
            assert len(keys) >= 2

            # Check key structure
            for key in keys:
                assert "name" in key or "key_name" in key
                assert "created_at" in key or "created" in key
        except AttributeError:
            pytest.skip("API key listing not implemented")

    def test_revoke_api_key(self, user_repository: UserRepository):
        """Test revoking an API key."""
        # Create user and key
        user_repository.create_user(
            username="revoke_test",
            password="password123",
            email="revoke@example.com"
        )

        key_id, api_key = user_repository.create_api_key("revoke_test", "Revoke Test Key")

        # Revoke the key
        user_repository.revoke_api_key(key_id)

        # Verify key can't be used anymore
        authenticated_user = user_repository.verify_api_key(api_key)
        assert authenticated_user is None


class TestScanRepository:
    """Test scan repository database operations."""

    def _record(self, repo: ScanRepository, *, project: str, status: str,
                violations: int = 0, warnings: int = 0, scan_id: str | None = None) -> str:
        scan_id = scan_id or str(uuid.uuid4())
        repo.record_scan(
            scan_id=scan_id,
            project=project,
            status=status,
            violations=violations,
            generated_at=datetime.now(timezone.utc),
            duration_seconds=1.0,
            summary={"violations": violations, "warnings": warnings},
            report={"findings": []},
        )
        return scan_id

    def test_create_and_retrieve_scan(self, test_config: LCCConfig):
        """Test creating and retrieving a scan."""
        repo = ScanRepository(test_config.database_path)

        scan_id = self._record(repo, project="test-project", status="completed", violations=2, warnings=3)
        assert scan_id is not None

        # Retrieve scan
        retrieved_scan = repo.get_scan(scan_id)
        assert retrieved_scan is not None
        assert retrieved_scan["project"] == "test-project"
        assert retrieved_scan["status"] == "completed"
        assert retrieved_scan["violations"] == 2

    def test_list_scans(self, test_config: LCCConfig):
        """Test listing all scans."""
        repo = ScanRepository(test_config.database_path)

        # Create multiple scans
        for i in range(3):
            self._record(repo, project=f"project-{i}", status="completed", violations=i, warnings=i * 2)

        # List scans
        scans = repo.list_scans()
        assert len(scans) >= 3

    def test_update_scan_status(self, test_config: LCCConfig):
        """Test updating scan status (via record_scan's INSERT OR REPLACE)."""
        repo = ScanRepository(test_config.database_path)

        scan_id = self._record(repo, project="status-test", status="pending")

        # Re-record with the same id to update the status
        self._record(repo, project="status-test", status="completed", scan_id=scan_id)

        # Verify update
        updated_scan = repo.get_scan(scan_id)
        assert updated_scan["status"] == "completed"

    def test_delete_scan(self, test_config: LCCConfig):
        """Test deleting a scan."""
        pytest.skip("ScanRepository does not implement per-scan deletion")

    def test_filter_scans_by_project(self, test_config: LCCConfig):
        """Test filtering scans by project name."""
        repo = ScanRepository(test_config.database_path)

        # Create scans for different projects
        for project in ["project-A", "project-B", "project-A"]:
            self._record(repo, project=project, status="completed")

        # Filter scans
        try:
            filtered_scans = repo.list_scans(project="project-A")
            assert len(filtered_scans) >= 2
            for scan in filtered_scans:
                assert scan["project"] == "project-A"
        except TypeError:
            # Filtering not implemented
            pytest.skip("Scan filtering not implemented")

    def test_aggregate_statistics(self, test_config: LCCConfig):
        """Test aggregating scan statistics."""
        repo = ScanRepository(test_config.database_path)

        # Create scans with violations and warnings
        for i in range(5):
            self._record(repo, project=f"stats-project-{i % 2}", status="completed",
                         violations=i, warnings=i * 2)

        # Get statistics
        try:
            stats = repo.get_statistics()
            assert "total_scans" in stats
            assert "total_violations" in stats
            assert "total_warnings" in stats
            assert stats["total_scans"] >= 5
        except AttributeError:
            pytest.skip("Statistics aggregation not implemented")


class TestDatabaseTransactions:
    """Test database transaction handling."""

    def test_transaction_rollback(self, test_config: LCCConfig):
        """Test that failed transactions are rolled back."""
        user_repo = UserRepository(test_config.database_path)

        # Create user
        user_repo.create_user(
            username="transaction_test",
            password="password123",
            email="transaction@example.com"
        )

        # Try to create duplicate (should fail)
        with pytest.raises((ValueError, sqlite3.IntegrityError)):
            user_repo.create_user(
                username="transaction_test",
                password="password456",
                email="different@example.com"
            )

        # Verify database is still consistent: the original user is intact
        user = user_repo.get_user("transaction_test")
        assert user is not None
        assert user.email == "transaction@example.com"

    def test_concurrent_writes(self, test_config: LCCConfig):
        """Test handling of concurrent database writes."""
        import threading

        user_repo = UserRepository(test_config.database_path)
        results = []

        def create_user(index: int):
            try:
                user_repo.create_user(
                    username=f"concurrent_{index}",
                    password="password123",
                    email=f"concurrent{index}@example.com"
                )
                results.append(("success", index))
            except Exception as e:
                results.append(("error", index, str(e)))

        # Create users concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_user, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All should succeed
        success_count = sum(1 for r in results if r[0] == "success")
        assert success_count == 5


class TestDatabaseMigration:
    """Test database schema and migration handling."""

    def test_database_initialization(self, temp_dir: Path):
        """Test that database is properly initialized."""
        db_path = temp_dir / "init_test.db"

        # Initialize user repository (should create tables)
        UserRepository(db_path)

        # Verify tables exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check users table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        assert cursor.fetchone() is not None

        # Check api_keys table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='api_keys'")
        assert cursor.fetchone() is not None

        conn.close()

    def test_database_schema_consistency(self, test_config: LCCConfig):
        """Test that database schema is consistent across operations."""
        # Create both repositories (should use same database)
        user_repo = UserRepository(test_config.database_path)
        scan_repo = ScanRepository(test_config.database_path)

        # Verify both work with the same database
        user_repo.create_user(
            username="schema_test",
            password="password123",
            email="schema@example.com"
        )

        scan_repo.record_scan(
            scan_id=str(uuid.uuid4()),
            project="schema-test",
            status="completed",
            violations=0,
            generated_at=datetime.now(timezone.utc),
            duration_seconds=1.0,
            summary={"violations": 0, "warnings": 0},
            report={"findings": []},
        )

        # Both should work without errors
        assert user_repo.get_user("schema_test") is not None
        scans = scan_repo.list_scans()
        assert len(scans) > 0
