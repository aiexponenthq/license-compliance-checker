"""Comprehensive tests for the license compatibility engine.

Tests cover:
- classify_license() mapping
- Copyleft contamination detection
- AGPL-in-SaaS detection
- SSPL-in-SaaS detection
- Copyleft version conflict detection
- Pairwise license conflict detection
- Weak copyleft boundary detection
- Unknown license handling
- evaluate_license_compatibility() entry point
- CompatibilityReport data model
"""

from __future__ import annotations

import pytest

from lcc.models import Component, ComponentFinding, ComponentType
from lcc.policy.compatibility import (
    CompatibilityIssue,
    CompatibilityReport,
    LicenseCompatibilityChecker,
    classify_license,
    evaluate_license_compatibility,
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


# ---------------------------------------------------------------------------
# a) Test classify_license()
# ---------------------------------------------------------------------------


class TestClassifyLicense:
    """Tests for classify_license() covering all license families."""

    @pytest.mark.parametrize(
        "license_id, expected_family",
        [
            ("MIT", "permissive"),
            ("Apache-2.0", "permissive"),
            ("BSD-3-Clause", "permissive"),
            ("BSD-2-Clause", "permissive"),
            ("ISC", "permissive"),
            ("Zlib", "permissive"),
            ("Unlicense", "permissive"),
            ("CC0-1.0", "permissive"),
            ("BSL-1.0", "permissive"),
            ("PSF-2.0", "permissive"),
        ],
    )
    def test_permissive_licenses(self, license_id: str, expected_family: str) -> None:
        assert classify_license(license_id) == expected_family

    @pytest.mark.parametrize(
        "license_id, expected_family",
        [
            ("GPL-3.0", "strong_copyleft"),
            ("GPL-3.0-only", "strong_copyleft"),
            ("GPL-3.0-or-later", "strong_copyleft"),
            ("GPL-2.0", "strong_copyleft"),
            ("GPL-2.0-only", "strong_copyleft"),
            ("GPL-2.0-or-later", "strong_copyleft"),
        ],
    )
    def test_strong_copyleft_licenses(self, license_id: str, expected_family: str) -> None:
        assert classify_license(license_id) == expected_family

    @pytest.mark.parametrize(
        "license_id, expected_family",
        [
            ("AGPL-3.0", "network_copyleft"),
            ("AGPL-3.0-only", "network_copyleft"),
            ("AGPL-3.0-or-later", "network_copyleft"),
        ],
    )
    def test_network_copyleft_licenses(self, license_id: str, expected_family: str) -> None:
        assert classify_license(license_id) == expected_family

    @pytest.mark.parametrize(
        "license_id, expected_family",
        [
            ("LGPL-2.1", "weak_copyleft"),
            ("LGPL-3.0", "weak_copyleft"),
            ("MPL-2.0", "weak_copyleft"),
            ("EPL-2.0", "weak_copyleft"),
        ],
    )
    def test_weak_copyleft_licenses(self, license_id: str, expected_family: str) -> None:
        assert classify_license(license_id) == expected_family

    def test_sspl_license(self) -> None:
        assert classify_license("SSPL-1.0") == "sspl"

    @pytest.mark.parametrize(
        "license_id",
        [
            "UNKNOWN",
            "NOASSERTION",
            "NONE",
            "",
        ],
    )
    def test_unknown_and_empty_licenses(self, license_id: str) -> None:
        assert classify_license(license_id) == "unknown"

    def test_none_license(self) -> None:
        # None is falsy, should return "unknown"
        assert classify_license(None) == "unknown"  # type: ignore[arg-type]

    def test_unrecognized_license_returns_unknown(self) -> None:
        assert classify_license("SomeProprietary-1.0") == "unknown"

    def test_wildcard_match_for_non_canonical_id(self) -> None:
        # Test that wildcard pattern matching works for IDs not in the exact sets
        # e.g. "Apache-1.1" is not in PERMISSIVE set but matches "Apache-*" pattern
        assert classify_license("Apache-1.1") == "permissive"

    def test_case_sensitivity(self) -> None:
        # SPDX identifiers are case-sensitive; "mit" would not be in the set
        # The classify_license only checks upper for UNKNOWN/NOASSERTION/NONE
        result = classify_license("mit")
        # "mit" is not in any set and doesn't match any pattern
        assert result == "unknown"


# ---------------------------------------------------------------------------
# b) Test copyleft contamination detection
# ---------------------------------------------------------------------------


class TestCopyleftContamination:
    """Tests for LicenseCompatibilityChecker.check_copyleft_contamination()."""

    def test_gpl3_contaminates_permissive_project(self) -> None:
        checker = LicenseCompatibilityChecker(project_license="Apache-2.0")
        findings = [_finding("gpl-lib", "GPL-3.0")]
        issues = checker.check_copyleft_contamination(findings)
        assert len(issues) == 1
        assert issues[0].severity == "critical"
        assert issues[0].issue_type == "copyleft_contamination"
        assert "GPL-3.0" in issues[0].description
        assert "Apache-2.0" in issues[0].description
        assert "gpl-lib" in issues[0].components
        assert issues[0].recommendation  # non-empty

    def test_mit_deps_no_contamination(self) -> None:
        checker = LicenseCompatibilityChecker(project_license="Apache-2.0")
        findings = [
            _finding("lib-a", "MIT"),
            _finding("lib-b", "MIT"),
        ]
        issues = checker.check_copyleft_contamination(findings)
        assert len(issues) == 0

    def test_no_project_license_returns_empty(self) -> None:
        checker = LicenseCompatibilityChecker(project_license=None)
        findings = [_finding("gpl-lib", "GPL-3.0")]
        issues = checker.check_copyleft_contamination(findings)
        assert len(issues) == 0

    def test_agpl_contaminates_permissive_project(self) -> None:
        checker = LicenseCompatibilityChecker(project_license="MIT")
        findings = [_finding("agpl-lib", "AGPL-3.0")]
        issues = checker.check_copyleft_contamination(findings)
        assert len(issues) == 1
        assert issues[0].severity == "critical"
        assert issues[0].issue_type == "copyleft_contamination"
        assert "network copyleft" in issues[0].description.lower()

    def test_sspl_contaminates_permissive_project(self) -> None:
        checker = LicenseCompatibilityChecker(project_license="MIT")
        findings = [_finding("sspl-db", "SSPL-1.0")]
        issues = checker.check_copyleft_contamination(findings)
        assert len(issues) == 1
        assert issues[0].severity == "critical"
        assert "SSPL" in issues[0].description

    def test_copyleft_project_not_contaminated_by_copyleft(self) -> None:
        """A GPL project using GPL deps should not trigger contamination."""
        checker = LicenseCompatibilityChecker(project_license="GPL-3.0")
        findings = [_finding("gpl-lib", "GPL-3.0")]
        issues = checker.check_copyleft_contamination(findings)
        assert len(issues) == 0

    def test_multiple_copyleft_deps_generate_multiple_issues(self) -> None:
        checker = LicenseCompatibilityChecker(project_license="Apache-2.0")
        findings = [
            _finding("gpl-lib", "GPL-3.0"),
            _finding("gpl2-lib", "GPL-2.0"),
        ]
        issues = checker.check_copyleft_contamination(findings)
        assert len(issues) == 2
        assert all(i.severity == "critical" for i in issues)

    def test_weak_copyleft_project_with_strong_copyleft_dep(self) -> None:
        """Weak copyleft project with strong copyleft dep triggers contamination."""
        checker = LicenseCompatibilityChecker(project_license="LGPL-2.1")
        findings = [_finding("gpl-lib", "GPL-3.0")]
        issues = checker.check_copyleft_contamination(findings)
        assert len(issues) == 1
        assert issues[0].severity == "critical"


# ---------------------------------------------------------------------------
# c) Test AGPL in SaaS detection
# ---------------------------------------------------------------------------


class TestAGPLInSaaS:
    """Tests for LicenseCompatibilityChecker.check_agpl_in_saas()."""

    def test_agpl_in_saas_context(self) -> None:
        checker = LicenseCompatibilityChecker(context="saas")
        findings = [_finding("agpl-lib", "AGPL-3.0")]
        issues = checker.check_agpl_in_saas(findings)
        assert len(issues) == 1
        assert issues[0].severity == "critical"
        assert issues[0].issue_type == "agpl_saas"
        assert "SaaS" in issues[0].description
        assert "AGPL-3.0" in issues[0].description
        assert issues[0].recommendation  # non-empty

    def test_mit_in_saas_no_issue(self) -> None:
        checker = LicenseCompatibilityChecker(context="saas")
        findings = [_finding("safe-lib", "MIT")]
        issues = checker.check_agpl_in_saas(findings)
        assert len(issues) == 0

    def test_agpl_in_non_saas_context_no_issue(self) -> None:
        checker = LicenseCompatibilityChecker(context="distributed")
        findings = [_finding("agpl-lib", "AGPL-3.0")]
        issues = checker.check_agpl_in_saas(findings)
        assert len(issues) == 0

    def test_agpl_with_no_context_no_issue(self) -> None:
        checker = LicenseCompatibilityChecker(context=None)
        findings = [_finding("agpl-lib", "AGPL-3.0")]
        issues = checker.check_agpl_in_saas(findings)
        assert len(issues) == 0

    def test_agpl_or_later_in_saas(self) -> None:
        checker = LicenseCompatibilityChecker(context="saas")
        findings = [_finding("agpl-or-later", "AGPL-3.0-or-later")]
        issues = checker.check_agpl_in_saas(findings)
        assert len(issues) == 1
        assert issues[0].severity == "critical"


# ---------------------------------------------------------------------------
# d) Test SSPL in SaaS detection
# ---------------------------------------------------------------------------


class TestSSPLInSaaS:
    """Tests for LicenseCompatibilityChecker.check_sspl_in_saas()."""

    def test_sspl_in_saas_context(self) -> None:
        checker = LicenseCompatibilityChecker(context="saas")
        findings = [_finding("mongo-driver", "SSPL-1.0")]
        issues = checker.check_sspl_in_saas(findings)
        assert len(issues) == 1
        assert issues[0].severity == "critical"
        assert issues[0].issue_type == "sspl_saas"
        assert "SSPL-1.0" in issues[0].description
        assert "service" in issues[0].description.lower()
        assert issues[0].recommendation  # non-empty

    def test_sspl_in_non_saas_no_issue(self) -> None:
        checker = LicenseCompatibilityChecker(context="internal")
        findings = [_finding("mongo-driver", "SSPL-1.0")]
        issues = checker.check_sspl_in_saas(findings)
        assert len(issues) == 0

    def test_sspl_with_no_context_no_issue(self) -> None:
        checker = LicenseCompatibilityChecker(context=None)
        findings = [_finding("mongo-driver", "SSPL-1.0")]
        issues = checker.check_sspl_in_saas(findings)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# e) Test copyleft version conflicts
# ---------------------------------------------------------------------------


class TestCopyleftVersionConflicts:
    """Tests for LicenseCompatibilityChecker.check_copyleft_version_conflicts()."""

    def test_gpl2_and_gpl3_conflict(self) -> None:
        checker = LicenseCompatibilityChecker()
        findings = [
            _finding("lib-gpl2", "GPL-2.0-only"),
            _finding("lib-gpl3", "GPL-3.0"),
        ]
        issues = checker.check_copyleft_version_conflicts(findings)
        assert len(issues) == 1
        assert issues[0].severity == "high"
        assert issues[0].issue_type == "copyleft_version_conflict"
        assert "GPL-2.0" in issues[0].description
        assert "GPL-3.0" in issues[0].description
        assert "lib-gpl2" in issues[0].components
        assert "lib-gpl3" in issues[0].components
        assert issues[0].recommendation  # non-empty

    def test_multiple_gpl3_no_conflict(self) -> None:
        checker = LicenseCompatibilityChecker()
        findings = [
            _finding("lib-a", "GPL-3.0"),
            _finding("lib-b", "GPL-3.0-only"),
        ]
        issues = checker.check_copyleft_version_conflicts(findings)
        assert len(issues) == 0

    def test_gpl2_only_no_conflict_among_gpl2(self) -> None:
        checker = LicenseCompatibilityChecker()
        findings = [
            _finding("lib-a", "GPL-2.0"),
            _finding("lib-b", "GPL-2.0-only"),
        ]
        issues = checker.check_copyleft_version_conflicts(findings)
        assert len(issues) == 0

    def test_no_gpl_deps_no_conflict(self) -> None:
        checker = LicenseCompatibilityChecker()
        findings = [
            _finding("lib-a", "MIT"),
            _finding("lib-b", "Apache-2.0"),
        ]
        issues = checker.check_copyleft_version_conflicts(findings)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# f) Test pairwise conflicts
# ---------------------------------------------------------------------------


class TestPairwiseConflicts:
    """Tests for LicenseCompatibilityChecker.check_pairwise_conflicts()."""

    def test_gpl2_and_apache2_conflict(self) -> None:
        checker = LicenseCompatibilityChecker()
        findings = [
            _finding("gpl2-lib", "GPL-2.0"),
            _finding("apache-lib", "Apache-2.0"),
        ]
        issues = checker.check_pairwise_conflicts(findings)
        assert len(issues) >= 1
        conflict_issue = issues[0]
        assert conflict_issue.severity == "high"
        assert conflict_issue.issue_type == "license_conflict"
        assert "GPL-2.0" in conflict_issue.description
        assert "Apache-2.0" in conflict_issue.description
        assert conflict_issue.recommendation  # non-empty

    def test_mit_and_apache2_no_conflict(self) -> None:
        checker = LicenseCompatibilityChecker()
        findings = [
            _finding("mit-lib", "MIT"),
            _finding("apache-lib", "Apache-2.0"),
        ]
        issues = checker.check_pairwise_conflicts(findings)
        assert len(issues) == 0

    def test_gpl2_only_and_apache2_conflict(self) -> None:
        checker = LicenseCompatibilityChecker()
        findings = [
            _finding("gpl-lib", "GPL-2.0-only"),
            _finding("apache-lib", "Apache-2.0"),
        ]
        issues = checker.check_pairwise_conflicts(findings)
        assert len(issues) >= 1

    def test_project_license_conflict_with_dependency(self) -> None:
        """Project licensed under GPL-2.0 with Apache-2.0 dep triggers conflict."""
        checker = LicenseCompatibilityChecker(project_license="GPL-2.0")
        findings = [_finding("apache-lib", "Apache-2.0")]
        issues = checker.check_pairwise_conflicts(findings)
        assert len(issues) >= 1
        assert any(i.issue_type == "license_conflict" for i in issues)

    def test_gpl3_and_apache2_no_pairwise_conflict(self) -> None:
        """GPL-3.0 IS compatible with Apache-2.0 (one-way)."""
        checker = LicenseCompatibilityChecker()
        findings = [
            _finding("gpl3-lib", "GPL-3.0"),
            _finding("apache-lib", "Apache-2.0"),
        ]
        issues = checker.check_pairwise_conflicts(findings)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# g) Test weak copyleft boundaries
# ---------------------------------------------------------------------------


class TestWeakCopyleftBoundaries:
    """Tests for LicenseCompatibilityChecker.check_weak_copyleft_boundaries()."""

    def test_lgpl_dynamic_linking_guidance(self) -> None:
        checker = LicenseCompatibilityChecker()
        findings = [_finding("lgpl-lib", "LGPL-2.1")]
        issues = checker.check_weak_copyleft_boundaries(findings)
        assert len(issues) == 1
        issue = issues[0]
        assert issue.severity == "medium"
        assert issue.issue_type == "weak_copyleft_boundary"
        assert "dynamic" in issue.description.lower() or "LGPL" in issue.description
        assert "dynamic" in issue.recommendation.lower()
        assert issue.recommendation  # non-empty

    def test_mpl_file_level_guidance(self) -> None:
        checker = LicenseCompatibilityChecker()
        findings = [_finding("mpl-lib", "MPL-2.0")]
        issues = checker.check_weak_copyleft_boundaries(findings)
        assert len(issues) == 1
        issue = issues[0]
        assert issue.severity == "medium"
        assert issue.issue_type == "weak_copyleft_boundary"
        assert "MPL" in issue.description
        assert "file" in issue.description.lower()
        assert "file" in issue.recommendation.lower() or "MPL" in issue.recommendation
        assert issue.recommendation  # non-empty

    def test_epl_boundary_guidance(self) -> None:
        checker = LicenseCompatibilityChecker()
        findings = [_finding("epl-lib", "EPL-2.0")]
        issues = checker.check_weak_copyleft_boundaries(findings)
        assert len(issues) == 1
        issue = issues[0]
        assert issue.severity == "medium"
        assert "EPL" in issue.description
        assert issue.recommendation  # non-empty

    def test_no_weak_copyleft_no_issues(self) -> None:
        checker = LicenseCompatibilityChecker()
        findings = [
            _finding("mit-lib", "MIT"),
            _finding("apache-lib", "Apache-2.0"),
        ]
        issues = checker.check_weak_copyleft_boundaries(findings)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# h) Test unknown license handling
# ---------------------------------------------------------------------------


class TestUnknownLicenses:
    """Tests for LicenseCompatibilityChecker.check_unknown_licenses()."""

    def test_unknown_resolved_license(self) -> None:
        checker = LicenseCompatibilityChecker()
        findings = [_finding("mystery-lib", "UNKNOWN")]
        issues = checker.check_unknown_licenses(findings)
        assert len(issues) == 1
        issue = issues[0]
        assert issue.severity == "low"
        assert issue.issue_type == "unknown_license"
        assert "mystery-lib" in issue.description
        assert issue.recommendation  # non-empty

    def test_none_resolved_license(self) -> None:
        checker = LicenseCompatibilityChecker()
        findings = [_finding("no-license-lib", None)]
        issues = checker.check_unknown_licenses(findings)
        assert len(issues) == 1
        issue = issues[0]
        assert issue.severity == "low"
        assert issue.issue_type == "unknown_license"

    def test_unrecognized_license_string(self) -> None:
        checker = LicenseCompatibilityChecker()
        findings = [_finding("custom-lib", "CustomProprietary-1.0")]
        issues = checker.check_unknown_licenses(findings)
        assert len(issues) == 1
        issue = issues[0]
        assert issue.severity == "low"
        assert "CustomProprietary-1.0" in issue.description

    def test_known_license_no_unknown_issue(self) -> None:
        checker = LicenseCompatibilityChecker()
        findings = [_finding("mit-lib", "MIT")]
        issues = checker.check_unknown_licenses(findings)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# i) Test evaluate_license_compatibility() entry point
# ---------------------------------------------------------------------------


class TestEvaluateLicenseCompatibility:
    """Tests for the evaluate_license_compatibility() convenience function."""

    def test_mixed_licenses_returns_report(self) -> None:
        findings = [
            _finding("gpl-lib", "GPL-3.0"),
            _finding("mit-lib", "MIT"),
            _finding("lgpl-lib", "LGPL-2.1"),
        ]
        report = evaluate_license_compatibility(
            findings, project_license="Apache-2.0", context="saas"
        )
        assert isinstance(report, CompatibilityReport)
        assert report.project_license == "Apache-2.0"
        assert report.context == "saas"
        # GPL-3.0 in permissive project should cause a critical issue
        assert any(i.severity == "critical" for i in report.issues)
        assert report.compatible is False

    def test_empty_findings_compatible(self) -> None:
        report = evaluate_license_compatibility(
            findings=[], project_license="MIT", context="internal"
        )
        assert isinstance(report, CompatibilityReport)
        assert report.compatible is True
        assert len(report.issues) == 0

    def test_report_to_dict_serialization(self) -> None:
        findings = [
            _finding("gpl-lib", "GPL-3.0"),
            _finding("mit-lib", "MIT"),
        ]
        report = evaluate_license_compatibility(
            findings, project_license="Apache-2.0"
        )
        d = report.to_dict()
        assert isinstance(d, dict)
        assert "project_license" in d
        assert "context" in d
        assert "issues" in d
        assert "compatible" in d
        assert "summary" in d
        assert isinstance(d["issues"], list)
        if d["issues"]:
            issue_dict = d["issues"][0]
            assert "severity" in issue_dict
            assert "issue_type" in issue_dict
            assert "description" in issue_dict
            assert "components" in issue_dict
            assert "licenses" in issue_dict
            assert "recommendation" in issue_dict

    def test_all_permissive_deps_compatible(self) -> None:
        findings = [
            _finding("mit-lib", "MIT"),
            _finding("bsd-lib", "BSD-3-Clause"),
            _finding("apache-lib", "Apache-2.0"),
        ]
        report = evaluate_license_compatibility(
            findings, project_license="MIT"
        )
        assert report.compatible is True
        # Only possible issues are weak_copyleft or unknown; none apply here
        critical_high = [i for i in report.issues if i.severity in ("critical", "high")]
        assert len(critical_high) == 0


# ---------------------------------------------------------------------------
# j) Test CompatibilityReport
# ---------------------------------------------------------------------------


class TestCompatibilityReport:
    """Tests for the CompatibilityReport data model."""

    def test_compatible_when_no_critical_or_high(self) -> None:
        report = CompatibilityReport(
            project_license="MIT",
            context=None,
            issues=[
                CompatibilityIssue(
                    severity="medium",
                    issue_type="weak_copyleft_boundary",
                    description="A medium issue.",
                    components=["lib-a"],
                    licenses=["LGPL-2.1"],
                    recommendation="Use dynamic linking.",
                ),
                CompatibilityIssue(
                    severity="low",
                    issue_type="unknown_license",
                    description="A low issue.",
                    components=["lib-b"],
                    licenses=["UNKNOWN"],
                    recommendation="Investigate license.",
                ),
            ],
        )
        assert report.compatible is True

    def test_incompatible_when_critical_issues_exist(self) -> None:
        report = CompatibilityReport(
            project_license="Apache-2.0",
            context=None,
            issues=[
                CompatibilityIssue(
                    severity="critical",
                    issue_type="copyleft_contamination",
                    description="GPL contamination.",
                    components=["gpl-lib"],
                    licenses=["GPL-3.0", "Apache-2.0"],
                    recommendation="Replace the dependency.",
                ),
            ],
        )
        assert report.compatible is False

    def test_incompatible_when_high_issues_exist(self) -> None:
        report = CompatibilityReport(
            project_license=None,
            context=None,
            issues=[
                CompatibilityIssue(
                    severity="high",
                    issue_type="copyleft_version_conflict",
                    description="GPL version conflict.",
                    components=["a", "b"],
                    licenses=["GPL-2.0", "GPL-3.0"],
                    recommendation="Unify versions.",
                ),
            ],
        )
        assert report.compatible is False

    def test_summary_counts_correct(self) -> None:
        report = CompatibilityReport(
            project_license="MIT",
            context="saas",
            issues=[
                CompatibilityIssue(
                    severity="critical",
                    issue_type="agpl_saas",
                    description="AGPL in SaaS.",
                    components=["agpl-lib"],
                    licenses=["AGPL-3.0"],
                    recommendation="Replace it.",
                ),
                CompatibilityIssue(
                    severity="critical",
                    issue_type="copyleft_contamination",
                    description="GPL contamination.",
                    components=["gpl-lib"],
                    licenses=["GPL-3.0"],
                    recommendation="Replace it.",
                ),
                CompatibilityIssue(
                    severity="high",
                    issue_type="license_conflict",
                    description="Pair conflict.",
                    components=["a", "b"],
                    licenses=["GPL-2.0", "Apache-2.0"],
                    recommendation="Fix it.",
                ),
                CompatibilityIssue(
                    severity="medium",
                    issue_type="weak_copyleft_boundary",
                    description="Weak copyleft.",
                    components=["lgpl-lib"],
                    licenses=["LGPL-2.1"],
                    recommendation="Dynamic link.",
                ),
                CompatibilityIssue(
                    severity="low",
                    issue_type="unknown_license",
                    description="Unknown.",
                    components=["x"],
                    licenses=["UNKNOWN"],
                    recommendation="Check it.",
                ),
            ],
        )
        assert report.summary["critical"] == 2
        assert report.summary["high"] == 1
        assert report.summary["medium"] == 1
        assert report.summary["low"] == 1
        assert report.compatible is False

    def test_to_dict_returns_valid_dict(self) -> None:
        report = CompatibilityReport(
            project_license="Apache-2.0",
            context="distributed",
            issues=[
                CompatibilityIssue(
                    severity="low",
                    issue_type="unknown_license",
                    description="Unknown license.",
                    components=["lib-x"],
                    licenses=["UNKNOWN"],
                    recommendation="Investigate.",
                ),
            ],
        )
        d = report.to_dict()
        assert isinstance(d, dict)
        assert d["project_license"] == "Apache-2.0"
        assert d["context"] == "distributed"
        assert d["compatible"] is True
        assert isinstance(d["summary"], dict)
        assert d["summary"]["critical"] == 0
        assert d["summary"]["low"] == 1
        assert len(d["issues"]) == 1
        assert d["issues"][0]["severity"] == "low"

    def test_empty_report(self) -> None:
        report = CompatibilityReport(
            project_license=None,
            context=None,
            issues=[],
        )
        assert report.compatible is True
        assert report.summary == {"critical": 0, "high": 0, "medium": 0, "low": 0}
        d = report.to_dict()
        assert d["issues"] == []

    def test_issue_to_dict(self) -> None:
        issue = CompatibilityIssue(
            severity="critical",
            issue_type="agpl_saas",
            description="AGPL in SaaS.",
            components=["agpl-lib"],
            licenses=["AGPL-3.0"],
            recommendation="Replace.",
        )
        d = issue.to_dict()
        assert d["severity"] == "critical"
        assert d["issue_type"] == "agpl_saas"
        assert d["description"] == "AGPL in SaaS."
        assert d["components"] == ["agpl-lib"]
        assert d["licenses"] == ["AGPL-3.0"]
        assert d["recommendation"] == "Replace."


# ---------------------------------------------------------------------------
# Additional edge-case tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Additional edge-case coverage."""

    def test_finding_with_noassertion_treated_as_unknown(self) -> None:
        checker = LicenseCompatibilityChecker()
        findings = [_finding("noassert-lib", "NOASSERTION")]
        issues = checker.check_unknown_licenses(findings)
        assert len(issues) == 1
        assert issues[0].issue_type == "unknown_license"

    def test_full_check_compatibility_runs_all_checks(self) -> None:
        """check_compatibility aggregates all sub-checks."""
        checker = LicenseCompatibilityChecker(
            project_license="Apache-2.0", context="saas"
        )
        findings = [
            _finding("gpl-lib", "GPL-3.0"),          # contamination
            _finding("agpl-lib", "AGPL-3.0"),         # AGPL SaaS + contamination
            _finding("unknown-lib", "UNKNOWN"),        # unknown
            _finding("lgpl-lib", "LGPL-2.1"),          # weak copyleft
        ]
        report = checker.check_compatibility(findings)
        issue_types = {i.issue_type for i in report.issues}
        assert "copyleft_contamination" in issue_types
        assert "agpl_saas" in issue_types
        assert "unknown_license" in issue_types
        assert "weak_copyleft_boundary" in issue_types
        assert report.compatible is False

    def test_descriptions_are_plain_english(self) -> None:
        """Verify descriptions contain readable English, not just codes."""
        checker = LicenseCompatibilityChecker(
            project_license="Apache-2.0", context="saas"
        )
        findings = [
            _finding("gpl-lib", "GPL-3.0"),
            _finding("agpl-lib", "AGPL-3.0"),
            _finding("sspl-lib", "SSPL-1.0"),
            _finding("lgpl-lib", "LGPL-2.1"),
            _finding("mpl-lib", "MPL-2.0"),
            _finding("unknown-lib", None),
        ]
        report = checker.check_compatibility(findings)
        for issue in report.issues:
            # Each description should be a real sentence with spaces
            assert len(issue.description) > 20, (
                f"Description too short: {issue.description}"
            )
            assert " " in issue.description, (
                f"Description not plain English: {issue.description}"
            )
            # Recommendations should also be present
            assert len(issue.recommendation) > 10, (
                f"Recommendation too short: {issue.recommendation}"
            )

    def test_recompute_updates_after_issue_append(self) -> None:
        """Verify _recompute() updates summary and compatible flag."""
        report = CompatibilityReport(
            project_license="MIT",
            context=None,
            issues=[],
        )
        assert report.compatible is True
        assert report.summary["critical"] == 0

        # Manually add an issue and recompute
        report.issues.append(
            CompatibilityIssue(
                severity="critical",
                issue_type="test",
                description="Test issue.",
                components=["x"],
                licenses=["GPL-3.0"],
                recommendation="Fix.",
            )
        )
        report._recompute()
        assert report.compatible is False
        assert report.summary["critical"] == 1
