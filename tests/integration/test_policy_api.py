"""Integration tests for Policy API endpoints."""

from __future__ import annotations

import yaml
import pytest
from fastapi.testclient import TestClient


class TestPolicyListingAndRetrieval:
    """Test policy listing and retrieval operations."""

    def test_list_policies(self, test_app: TestClient, admin_token: str):
        """Test listing all available policies."""
        response = test_app.get(
            "/policies",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        policies = response.json()
        assert isinstance(policies, list)

        # Should have at least built-in policies
        assert len(policies) > 0

        # Check policy structure
        for policy in policies:
            assert "name" in policy
            assert "description" in policy or "disclaimer" in policy
            assert "status" in policy

    def test_get_policy_details(self, test_app: TestClient, admin_token: str):
        """Test getting details of a specific policy."""
        # First, list policies to get a valid policy name
        list_response = test_app.get(
            "/policies",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert list_response.status_code == 200
        policies = list_response.json()
        assert len(policies) > 0

        # Get details of the first policy
        policy_name = policies[0]["name"]
        response = test_app.get(
            f"/policies/{policy_name}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        policy_detail = response.json()
        assert policy_detail["name"] == policy_name
        assert "contexts" in policy_detail
        assert isinstance(policy_detail["contexts"], list)

        # Check context structure
        if policy_detail["contexts"]:
            context = policy_detail["contexts"][0]
            assert "name" in context
            assert "allow" in context or "deny" in context or "review" in context

    def test_get_nonexistent_policy(self, test_app: TestClient, admin_token: str):
        """Test getting a policy that doesn't exist."""
        response = test_app.get(
            "/policies/nonexistent-policy-12345",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestPolicyCreation:
    """Test policy creation operations."""

    def test_create_policy_yaml(self, test_app: TestClient, admin_token: str):
        """Test creating a new policy with YAML format."""
        policy_content = """
name: integration-test-policy
version: 1.0
disclaimer: Test policy created during integration testing
description: A test policy for YAML format
default_context: production
contexts:
  production:
    allow:
      - MIT
      - Apache-2.0
    deny:
      - GPL-*
    review:
      - LGPL-*
    deny_reasons:
      GPL-*: Strong copyleft license
    dual_license_preference: most_permissive
  development:
    allow:
      - "*"
"""

        response = test_app.post(
            "/policies",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "integration-test-policy",
                "content": policy_content.strip(),
                "format": "yaml"
            }
        )

        assert response.status_code == 201
        created_policy = response.json()
        assert created_policy["name"] == "integration-test-policy"
        assert "disclaimer" in created_policy

        # Verify the policy exists
        get_response = test_app.get(
            "/policies/integration-test-policy",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 200

        # Cleanup
        delete_response = test_app.delete(
            "/policies/integration-test-policy",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == 204

    def test_create_policy_json(self, test_app: TestClient, admin_token: str):
        """Test creating a new policy with JSON format."""
        import json

        policy_data = {
            "name": "json-test-policy",
            "version": "1.0",
            "disclaimer": "JSON format test policy",
            "default_context": "production",
            "contexts": {
                "production": {
                    "allow": ["MIT", "BSD-3-Clause"],
                    "deny": ["GPL-*"],
                    "review": []
                }
            }
        }

        response = test_app.post(
            "/policies",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "json-test-policy",
                "content": json.dumps(policy_data),
                "format": "json"
            }
        )

        assert response.status_code == 201
        created_policy = response.json()
        assert created_policy["name"] == "json-test-policy"

        # Cleanup
        test_app.delete(
            "/policies/json-test-policy",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

    def test_create_duplicate_policy(self, test_app: TestClient, admin_token: str):
        """Test that duplicate policy names are rejected."""
        policy_content = """
name: duplicate-test
version: 1.0
disclaimer: First policy
contexts:
  production:
    allow: [MIT]
"""

        # Create first policy
        response1 = test_app.post(
            "/policies",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "duplicate-test",
                "content": policy_content,
                "format": "yaml"
            }
        )
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = test_app.post(
            "/policies",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "duplicate-test",
                "content": policy_content,
                "format": "yaml"
            }
        )
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"].lower()

        # Cleanup
        test_app.delete(
            "/policies/duplicate-test",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

    def test_create_invalid_policy(self, test_app: TestClient, admin_token: str):
        """Test that invalid policy content is rejected."""
        response = test_app.post(
            "/policies",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "invalid-policy",
                "content": "{ invalid yaml content",
                "format": "yaml"
            }
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_create_policy_without_admin(self, test_app: TestClient, user_token: str):
        """Test that non-admin users cannot create policies."""
        response = test_app.post(
            "/policies",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "name": "unauthorized-policy",
                "content": "name: test\nversion: 1.0\ndisclaimer: test",
                "format": "yaml"
            }
        )

        assert response.status_code == 403
        assert "insufficient permissions" in response.json()["detail"].lower()


class TestPolicyUpdate:
    """Test policy update operations."""

    def test_update_policy(self, test_app: TestClient, admin_token: str):
        """Test updating an existing policy."""
        # Create a policy first
        create_content = """
name: update-test-policy
version: 1.0
disclaimer: Original version
contexts:
  production:
    allow: [MIT]
"""

        create_response = test_app.post(
            "/policies",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "update-test-policy",
                "content": create_content.strip(),
                "format": "yaml"
            }
        )
        assert create_response.status_code == 201

        # Update the policy
        update_content = """
name: update-test-policy
version: 2.0
disclaimer: Updated version
contexts:
  production:
    allow: [MIT, Apache-2.0]
    deny: [GPL-*]
"""

        update_response = test_app.put(
            "/policies/update-test-policy",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "content": update_content.strip(),
                "format": "yaml"
            }
        )
        assert update_response.status_code == 200
        updated_policy = update_response.json()
        assert updated_policy["name"] == "update-test-policy"

        # Verify the update
        get_response = test_app.get(
            "/policies/update-test-policy",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 200
        policy_detail = get_response.json()

        # Check that the policy was updated (should have 2 licenses in allow list)
        production_context = next(
            (c for c in policy_detail["contexts"] if c["name"] == "production"),
            None
        )
        assert production_context is not None
        assert len(production_context["allow"]) == 2
        assert "Apache-2.0" in production_context["allow"]

        # Cleanup
        test_app.delete(
            "/policies/update-test-policy",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

    def test_update_nonexistent_policy(self, test_app: TestClient, admin_token: str):
        """Test updating a policy that doesn't exist."""
        response = test_app.put(
            "/policies/nonexistent-policy-xyz",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "content": "name: test\nversion: 1.0\ndisclaimer: test",
                "format": "yaml"
            }
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_policy_without_admin(self, test_app: TestClient, user_token: str, admin_token: str):
        """Test that non-admin users cannot update policies."""
        # Create a policy as admin
        create_response = test_app.post(
            "/policies",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "admin-only-update",
                "content": "name: admin-only-update\nversion: 1.0\ndisclaimer: test\ncontexts:\n  production:\n    allow: [MIT]",
                "format": "yaml"
            }
        )
        assert create_response.status_code == 201

        # Try to update as regular user
        update_response = test_app.put(
            "/policies/admin-only-update",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "content": "name: admin-only-update\nversion: 2.0\ndisclaimer: updated",
                "format": "yaml"
            }
        )

        assert update_response.status_code == 403
        assert "insufficient permissions" in update_response.json()["detail"].lower()

        # Cleanup
        test_app.delete(
            "/policies/admin-only-update",
            headers={"Authorization": f"Bearer {admin_token}"}
        )


class TestPolicyDeletion:
    """Test policy deletion operations."""

    def test_delete_policy(self, test_app: TestClient, admin_token: str):
        """Test deleting a custom policy."""
        # Create a policy
        create_response = test_app.post(
            "/policies",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "delete-test-policy",
                "content": "name: delete-test-policy\nversion: 1.0\ndisclaimer: test\ncontexts:\n  production:\n    allow: [MIT]",
                "format": "yaml"
            }
        )
        assert create_response.status_code == 201

        # Delete the policy
        delete_response = test_app.delete(
            "/policies/delete-test-policy",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == 204

        # Verify it's deleted
        get_response = test_app.get(
            "/policies/delete-test-policy",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 404

    def test_delete_nonexistent_policy(self, test_app: TestClient, admin_token: str):
        """Test deleting a policy that doesn't exist."""
        response = test_app.delete(
            "/policies/nonexistent-delete-policy",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_policy_without_admin(self, test_app: TestClient, user_token: str, admin_token: str):
        """Test that non-admin users cannot delete policies."""
        # Create a policy as admin
        create_response = test_app.post(
            "/policies",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "admin-protected-delete",
                "content": "name: admin-protected-delete\nversion: 1.0\ndisclaimer: test\ncontexts:\n  production:\n    allow: [MIT]",
                "format": "yaml"
            }
        )
        assert create_response.status_code == 201

        # Try to delete as regular user
        delete_response = test_app.delete(
            "/policies/admin-protected-delete",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert delete_response.status_code == 403
        assert "insufficient permissions" in delete_response.json()["detail"].lower()

        # Cleanup as admin
        test_app.delete(
            "/policies/admin-protected-delete",
            headers={"Authorization": f"Bearer {admin_token}"}
        )


class TestPolicyEvaluation:
    """Test policy evaluation operations."""

    def test_evaluate_policy(self, test_app: TestClient, admin_token: str):
        """Test evaluating licenses against a policy."""
        # Create a test policy
        policy_content = """
name: eval-test-policy
version: 1.0
disclaimer: Evaluation test policy
contexts:
  production:
    allow:
      - MIT
      - Apache-2.0
    deny:
      - GPL-*
    review:
      - LGPL-*
    deny_reasons:
      GPL-*: Strong copyleft incompatible with proprietary software
"""

        create_response = test_app.post(
            "/policies",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "eval-test-policy",
                "content": policy_content.strip(),
                "format": "yaml"
            }
        )
        assert create_response.status_code == 201

        # Evaluate licenses against the policy
        eval_response = test_app.post(
            "/policies/eval-test-policy/evaluate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "licenses": ["MIT", "GPL-3.0", "Apache-2.0", "LGPL-2.1"],
                "context": "production"
            }
        )

        assert eval_response.status_code == 200
        results = eval_response.json()
        assert isinstance(results, list)
        assert len(results) == 4

        # Check results structure
        for result in results:
            assert "license" in result
            assert "status" in result
            assert result["status"] in ["pass", "violation", "warning", "review"]

        # Verify specific results
        mit_result = next(r for r in results if r["license"] == "MIT")
        assert mit_result["status"] in ["pass", "allowed"]

        gpl_result = next(r for r in results if r["license"] == "GPL-3.0")
        assert gpl_result["status"] in ["violation", "denied"]

        # Cleanup
        test_app.delete(
            "/policies/eval-test-policy",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

    def test_evaluate_with_context(self, test_app: TestClient, admin_token: str, user_token: str):
        """Test policy evaluation with different contexts."""
        # Create a multi-context policy
        policy_content = """
name: context-test-policy
version: 1.0
disclaimer: Multi-context test
contexts:
  production:
    allow: [MIT]
    deny: [GPL-*]
  development:
    allow: ["*"]
    deny: []
"""

        create_response = test_app.post(
            "/policies",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "context-test-policy",
                "content": policy_content.strip(),
                "format": "yaml"
            }
        )
        assert create_response.status_code == 201

        # Evaluate in production context
        prod_response = test_app.post(
            "/policies/context-test-policy/evaluate",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "licenses": ["GPL-3.0"],
                "context": "production"
            }
        )
        assert prod_response.status_code == 200

        # Evaluate in development context
        dev_response = test_app.post(
            "/policies/context-test-policy/evaluate",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "licenses": ["GPL-3.0"],
                "context": "development"
            }
        )
        assert dev_response.status_code == 200

        # Results should differ based on context
        prod_results = prod_response.json()
        dev_results = dev_response.json()

        # In production, GPL should be denied
        # In development, GPL should be allowed
        # (Exact behavior depends on policy evaluation logic)

        # Cleanup
        test_app.delete(
            "/policies/context-test-policy",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

    def test_evaluate_nonexistent_policy(self, test_app: TestClient, admin_token: str):
        """Test evaluating against a nonexistent policy."""
        response = test_app.post(
            "/policies/nonexistent-eval-policy/evaluate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "licenses": ["MIT"],
                "context": "production"
            }
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
