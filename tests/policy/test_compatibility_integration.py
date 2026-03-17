"""Tests for the compatibility integration layer.

Covers:
- run_compatibility_check() with various policy configurations
- policy_has_compatibility() predicate
"""

from __future__ import annotations

import pytest

from lcc.models import Component, ComponentFinding, ComponentType
from lcc.policy.compatibility import CompatibilityReport
from lcc.policy.compatibility_integration import (
    policy_has_compatibility,
    run_compatibility_check,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _finding(name: str, license_id: str | None) -> ComponentFinding:
    """Create a minimal ComponentFinding for testing."""
    return ComponentFinding(
        component=Component(
            type=ComponentType.PYTHON,
            name=name,
            version="1.0.0",
        ),
        resolved_license=license_id,
    )


def _policy_with_compat(**overrides) -> dict:
    """Return a policy dict with a compatibility section.

    Any keyword arguments override defaults in the compatibility section.
    """
    compat = {
        "project_license": "Apache-2.0",
        "check_contamination": True,
        "check_agpl_saas": True,
        "check_pairwise": True,
        "check_weak_copyleft": True,
    }
    compat.update(overrides)
    return {
        "name": "test-policy",
        "compatibility": compat,
    }


def _policy_without_compat() -> dict:
    """Return a policy dict with no compatibility section."""
    return {
        "name": "test-policy",
        "contexts": {"internal": {"allow": ["MIT"]}},
    }


# ---------------------------------------------------------------------------
# a) Test run_compatibility_check()
# ---------------------------------------------------------------------------


class TestRunCompatibilityCheck:
    """Tests for run_compatibility_check()."""

    def test_with_compatibility_section_runs_check(self) -> None:
        """Policy with a compatibility section should produce a full report."""
        policy = _policy_with_compat()
        findings = [
            _finding("gpl-lib", "GPL-3.0"),
            _finding("mit-lib", "MIT"),
        ]
        report = run_compatibility_check(
            findings, policy=policy, context="distributed"
        )
        assert isinstance(report, CompatibilityReport)
        # GPL-3.0 in an Apache-2.0 project -> contamination
        assert any(
            i.issue_type == "copyleft_contamination" for i in report.issues
        )
        assert report.compatible is False

    def test_without_compatibility_section_uses_defaults(self) -> None:
        """Policy without compatibility section should still run with defaults."""
        policy = _policy_without_compat()
        findings = [
            _finding("mit-lib", "MIT"),
            _finding("unknown-lib", None),
        ]
        report = run_compatibility_check(
            findings, policy=policy, context="internal"
        )
        assert isinstance(report, CompatibilityReport)
        # No critical issues from MIT + unknown, but unknown flagged
        assert any(i.issue_type == "unknown_license" for i in report.issues)

    def test_none_policy_uses_defaults(self) -> None:
        """Passing None as policy should still work with all checks enabled."""
        findings = [
            _finding("lgpl-lib", "LGPL-2.1"),
        ]
        report = run_compatibility_check(
            findings, policy=None, context=None
        )
        assert isinstance(report, CompatibilityReport)
        # LGPL should trigger weak_copyleft_boundary
        assert any(
            i.issue_type == "weak_copyleft_boundary" for i in report.issues
        )

    def test_check_contamination_false_skips_contamination(self) -> None:
        """Setting check_contamination=False should skip copyleft contamination."""
        policy = _policy_with_compat(check_contamination=False)
        findings = [
            _finding("gpl-lib", "GPL-3.0"),
        ]
        report = run_compatibility_check(
            findings, policy=policy, context="distributed"
        )
        # Contamination check was disabled, so no copyleft_contamination issues
        contamination_issues = [
            i for i in report.issues if i.issue_type == "copyleft_contamination"
        ]
        assert len(contamination_issues) == 0

    def test_check_agpl_saas_false_skips_agpl_and_sspl_saas(self) -> None:
        """Setting check_agpl_saas=False should skip AGPL and SSPL SaaS checks."""
        policy = _policy_with_compat(check_agpl_saas=False)
        findings = [
            _finding("agpl-lib", "AGPL-3.0"),
            _finding("sspl-lib", "SSPL-1.0"),
        ]
        report = run_compatibility_check(
            findings, policy=policy, context="saas"
        )
        agpl_saas_issues = [
            i for i in report.issues if i.issue_type in ("agpl_saas", "sspl_saas")
        ]
        assert len(agpl_saas_issues) == 0

    def test_check_pairwise_false_skips_pairwise_conflicts(self) -> None:
        """Setting check_pairwise=False should skip pairwise conflict checks."""
        policy = _policy_with_compat(
            check_pairwise=False,
            check_contamination=False,
            project_license=None,
        )
        findings = [
            _finding("gpl2-lib", "GPL-2.0"),
            _finding("apache-lib", "Apache-2.0"),
        ]
        report = run_compatibility_check(
            findings, policy=policy, context="distributed"
        )
        pairwise_issues = [
            i for i in report.issues if i.issue_type == "license_conflict"
        ]
        assert len(pairwise_issues) == 0

    def test_check_weak_copyleft_false_skips_weak_copyleft(self) -> None:
        """Setting check_weak_copyleft=False should skip weak copyleft checks."""
        policy = _policy_with_compat(check_weak_copyleft=False, project_license=None)
        findings = [
            _finding("lgpl-lib", "LGPL-2.1"),
            _finding("mpl-lib", "MPL-2.0"),
        ]
        report = run_compatibility_check(
            findings, policy=policy, context="internal"
        )
        weak_issues = [
            i for i in report.issues if i.issue_type == "weak_copyleft_boundary"
        ]
        assert len(weak_issues) == 0

    def test_cli_project_license_overrides_policy(self) -> None:
        """project_license argument should override the policy's value."""
        policy = _policy_with_compat(project_license="GPL-3.0")
        findings = [_finding("gpl-lib", "GPL-3.0")]
        # With policy's GPL-3.0, no contamination. Override to MIT -> contamination.
        report = run_compatibility_check(
            findings, policy=policy, project_license="MIT"
        )
        assert report.project_license == "MIT"
        assert any(
            i.issue_type == "copyleft_contamination" for i in report.issues
        )

    def test_empty_findings_returns_compatible_report(self) -> None:
        policy = _policy_with_compat()
        report = run_compatibility_check(
            findings=[], policy=policy, context="saas"
        )
        assert report.compatible is True
        assert len(report.issues) == 0

    def test_version_conflicts_always_checked(self) -> None:
        """Version conflicts are always checked, even with minimal policy."""
        policy = _policy_with_compat(
            check_contamination=False,
            check_agpl_saas=False,
            check_pairwise=False,
            check_weak_copyleft=False,
            project_license=None,
        )
        findings = [
            _finding("gpl2-lib", "GPL-2.0-only"),
            _finding("gpl3-lib", "GPL-3.0"),
        ]
        report = run_compatibility_check(findings, policy=policy)
        assert any(
            i.issue_type == "copyleft_version_conflict" for i in report.issues
        )

    def test_unknown_licenses_always_checked(self) -> None:
        """Unknown license check always runs, regardless of policy flags."""
        policy = _policy_with_compat(
            check_contamination=False,
            check_agpl_saas=False,
            check_pairwise=False,
            check_weak_copyleft=False,
            project_license=None,
        )
        findings = [_finding("mystery-lib", "UNKNOWN")]
        report = run_compatibility_check(findings, policy=policy)
        assert any(i.issue_type == "unknown_license" for i in report.issues)

    def test_report_context_matches_input(self) -> None:
        report = run_compatibility_check(
            findings=[], policy=None, context="saas"
        )
        assert report.context == "saas"

    def test_saas_context_with_agpl_and_sspl(self) -> None:
        """Full SaaS scenario with both AGPL and SSPL deps."""
        policy = _policy_with_compat(project_license="Apache-2.0")
        findings = [
            _finding("agpl-lib", "AGPL-3.0"),
            _finding("sspl-db", "SSPL-1.0"),
            _finding("mit-lib", "MIT"),
        ]
        report = run_compatibility_check(
            findings, policy=policy, context="saas"
        )
        issue_types = {i.issue_type for i in report.issues}
        assert "agpl_saas" in issue_types
        assert "sspl_saas" in issue_types
        assert "copyleft_contamination" in issue_types
        assert report.compatible is False


# ---------------------------------------------------------------------------
# b) Test policy_has_compatibility()
# ---------------------------------------------------------------------------


class TestPolicyHasCompatibility:
    """Tests for the policy_has_compatibility() predicate."""

    def test_policy_with_compatibility_key(self) -> None:
        policy = {"compatibility": {"project_license": "MIT"}}
        assert policy_has_compatibility(policy) is True

    def test_policy_with_empty_compatibility_dict(self) -> None:
        policy = {"compatibility": {}}
        assert policy_has_compatibility(policy) is True

    def test_policy_without_compatibility(self) -> None:
        policy = {"name": "test", "contexts": {}}
        assert policy_has_compatibility(policy) is False

    def test_none_policy(self) -> None:
        assert policy_has_compatibility(None) is False

    def test_empty_dict_policy(self) -> None:
        assert policy_has_compatibility({}) is False

    def test_compatibility_not_a_dict(self) -> None:
        """If compatibility is not a dict, return False."""
        policy = {"compatibility": "yes"}
        assert policy_has_compatibility(policy) is False

    def test_compatibility_is_list(self) -> None:
        policy = {"compatibility": ["check_contamination"]}
        assert policy_has_compatibility(policy) is False

    def test_non_dict_policy(self) -> None:
        """Non-dict policy returns False."""
        assert policy_has_compatibility("not a dict") is False  # type: ignore[arg-type]
