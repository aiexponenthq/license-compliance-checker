"""Tests for lcc.regulatory.reporter — JSON/HTML report generation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lcc.models import Component, ComponentFinding, ComponentType
from lcc.regulatory.eu_ai_act import EUAIActAssessor
from lcc.regulatory.frameworks import (
    AIRiskClassification,
    Article53Obligation,
    RegulatoryAssessment,
    RegulatoryFramework,
    RegulatoryReport,
)
from lcc.regulatory.reporter import (
    RegulatoryReporter,
    generate_compliance_pack,
)


# ------------------------------------------------------------------ #
#  Helpers                                                             #
# ------------------------------------------------------------------ #


def _make_finding(
    name: str = "test-model",
    version: str = "1.0.0",
    comp_type: ComponentType = ComponentType.AI_MODEL,
    resolved_license: str | None = None,
    metadata: dict | None = None,
) -> ComponentFinding:
    return ComponentFinding(
        component=Component(
            type=comp_type,
            name=name,
            version=version,
            metadata=metadata or {},
        ),
        resolved_license=resolved_license,
    )


def _make_sample_report() -> RegulatoryReport:
    """Create a sample report with one assessment for testing."""
    ob1 = Article53Obligation(
        article="Art.53(1)(a)",
        title="Technical documentation",
        description="Draw up docs.",
        status="met",
        evidence=["SBOM component entry", "Version: 2.0.0", "License: apache-2.0"],
    )
    ob2 = Article53Obligation(
        article="Art.53(1)(b)",
        title="Info for downstream providers",
        description="Provide info.",
        status="met",
        evidence=["License resolved: apache-2.0", "Metadata available"],
    )
    ob3 = Article53Obligation(
        article="Art.53(1)(c)",
        title="Copyright policy compliance",
        description="Copyright policy.",
        status="met",
        evidence=["License: apache-2.0"],
    )
    ob4 = Article53Obligation(
        article="Art.53(1)(d)",
        title="Training data summary",
        description="Training data summary.",
        status="not_met",
        gaps=["No training data summary available"],
    )
    ob5 = Article53Obligation(
        article="Art.53(2)",
        title="Systemic risk additional obligations",
        description="Systemic risk.",
        status="not_applicable",
        evidence=["Component not classified as GPAI with systemic risk"],
    )

    assessment = RegulatoryAssessment(
        framework=RegulatoryFramework.EU_AI_ACT,
        component_name="my-ai-model",
        component_type="ai_model",
        risk_classification=AIRiskClassification.GPAI,
        obligations=[ob1, ob2, ob3, ob4, ob5],
        overall_status="non_compliant",
        recommendations=[
            "[Art.53(1)(d)] Training data summary: Action required"
        ],
        assessed_at="2025-06-01T12:00:00",
    )

    return RegulatoryReport(
        title="EU AI Act Article 53 GPAI Compliance Report",
        framework=RegulatoryFramework.EU_AI_ACT,
        generated_at="2025-06-01T12:00:00",
        assessments=[assessment],
        summary={
            "total_ai_components": 1,
            "compliant": 0,
            "partial": 0,
            "non_compliant": 1,
            "compliance_percentage": 0.0,
        },
    )


def _make_empty_report() -> RegulatoryReport:
    """Create an empty report with no assessments."""
    return RegulatoryReport(
        title="EU AI Act Article 53 GPAI Compliance Report",
        framework=RegulatoryFramework.EU_AI_ACT,
        generated_at="2025-06-01T12:00:00",
        assessments=[],
        summary={
            "total_ai_components": 0,
            "compliant": 0,
            "partial": 0,
            "non_compliant": 0,
            "compliance_percentage": 0.0,
        },
    )


# ------------------------------------------------------------------ #
#  JSON output                                                         #
# ------------------------------------------------------------------ #


class TestRegulatoryReporterJSON:
    def test_to_json_creates_valid_file(self, tmp_path: Path):
        report = _make_sample_report()
        reporter = RegulatoryReporter(report)
        output = tmp_path / "report.json"

        reporter.to_json(output)

        assert output.exists()
        data = json.loads(output.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert data["title"] == "EU AI Act Article 53 GPAI Compliance Report"
        assert data["framework"] == "eu_ai_act"

    def test_to_json_has_assessments(self, tmp_path: Path):
        report = _make_sample_report()
        reporter = RegulatoryReporter(report)
        output = tmp_path / "report.json"

        reporter.to_json(output)
        data = json.loads(output.read_text(encoding="utf-8"))

        assert len(data["assessments"]) == 1
        assessment = data["assessments"][0]
        assert assessment["component_name"] == "my-ai-model"
        assert len(assessment["obligations"]) == 5

    def test_to_json_has_summary(self, tmp_path: Path):
        report = _make_sample_report()
        reporter = RegulatoryReporter(report)
        output = tmp_path / "report.json"

        reporter.to_json(output)
        data = json.loads(output.read_text(encoding="utf-8"))

        assert data["summary"]["total_ai_components"] == 1
        assert data["summary"]["non_compliant"] == 1

    def test_to_json_creates_parent_dirs(self, tmp_path: Path):
        report = _make_sample_report()
        reporter = RegulatoryReporter(report)
        output = tmp_path / "subdir" / "nested" / "report.json"

        reporter.to_json(output)
        assert output.exists()

    def test_to_json_empty_report(self, tmp_path: Path):
        report = _make_empty_report()
        reporter = RegulatoryReporter(report)
        output = tmp_path / "empty.json"

        reporter.to_json(output)
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["assessments"] == []
        assert data["summary"]["total_ai_components"] == 0


# ------------------------------------------------------------------ #
#  HTML output                                                         #
# ------------------------------------------------------------------ #


class TestRegulatoryReporterHTML:
    def test_to_html_creates_valid_file(self, tmp_path: Path):
        report = _make_sample_report()
        reporter = RegulatoryReporter(report)
        output = tmp_path / "report.html"

        reporter.to_html(output)

        assert output.exists()
        html = output.read_text(encoding="utf-8")
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_html_contains_compliance_score(self, tmp_path: Path):
        report = _make_sample_report()
        reporter = RegulatoryReporter(report)
        output = tmp_path / "report.html"

        reporter.to_html(output)
        html = output.read_text(encoding="utf-8")

        # Should contain the compliance percentage
        assert "0.0%" in html
        # Should contain "Overall Compliance" label
        assert "Overall Compliance" in html

    def test_html_contains_obligation_table(self, tmp_path: Path):
        report = _make_sample_report()
        reporter = RegulatoryReporter(report)
        output = tmp_path / "report.html"

        reporter.to_html(output)
        html = output.read_text(encoding="utf-8")

        # Should contain obligation table headers
        assert "Obligation" in html
        assert "Status" in html
        assert "Evidence" in html
        assert "Gaps" in html

        # Should contain specific article references
        assert "Art.53(1)(a)" in html
        assert "Art.53(1)(b)" in html
        assert "Art.53(1)(c)" in html
        assert "Art.53(1)(d)" in html
        assert "Art.53(2)" in html

    def test_html_contains_component_name(self, tmp_path: Path):
        report = _make_sample_report()
        reporter = RegulatoryReporter(report)
        output = tmp_path / "report.html"

        reporter.to_html(output)
        html = output.read_text(encoding="utf-8")

        assert "my-ai-model" in html

    def test_html_contains_recommendations(self, tmp_path: Path):
        report = _make_sample_report()
        reporter = RegulatoryReporter(report)
        output = tmp_path / "report.html"

        reporter.to_html(output)
        html = output.read_text(encoding="utf-8")

        assert "Recommendations" in html
        assert "Training data summary" in html

    def test_html_empty_report_shows_message(self, tmp_path: Path):
        report = _make_empty_report()
        reporter = RegulatoryReporter(report)
        output = tmp_path / "empty.html"

        reporter.to_html(output)
        html = output.read_text(encoding="utf-8")

        assert "No AI models or datasets were detected" in html

    def test_html_creates_parent_dirs(self, tmp_path: Path):
        report = _make_sample_report()
        reporter = RegulatoryReporter(report)
        output = tmp_path / "deep" / "nested" / "report.html"

        reporter.to_html(output)
        assert output.exists()


# ------------------------------------------------------------------ #
#  to_dict                                                             #
# ------------------------------------------------------------------ #


class TestRegulatoryReporterToDict:
    def test_to_dict(self):
        report = _make_sample_report()
        reporter = RegulatoryReporter(report)
        d = reporter.to_dict()

        assert isinstance(d, dict)
        assert d["title"] == "EU AI Act Article 53 GPAI Compliance Report"
        assert d["framework"] == "eu_ai_act"


# ------------------------------------------------------------------ #
#  generate_compliance_pack                                            #
# ------------------------------------------------------------------ #


class TestGenerateCompliancePack:
    def test_creates_directory_with_four_files(self, tmp_path: Path):
        report = _make_sample_report()
        findings = [
            _make_finding(
                name="my-ai-model",
                version="2.0.0",
                comp_type=ComponentType.AI_MODEL,
                resolved_license="apache-2.0",
                metadata={
                    "description": "A test model.",
                    "datasets": ["wikitext"],
                },
            ),
        ]

        pack_dir = generate_compliance_pack(report, findings, tmp_path)

        assert pack_dir.exists()
        assert pack_dir.is_dir()
        assert pack_dir.name.startswith("eu-ai-act-compliance-pack-")

        # Verify all 4 files exist
        json_report = pack_dir / "eu_ai_act_report.json"
        html_report = pack_dir / "eu_ai_act_report.html"
        training_summary = pack_dir / "training_data_summary.json"
        copyright_template = pack_dir / "copyright_policy_template.md"

        assert json_report.exists()
        assert html_report.exists()
        assert training_summary.exists()
        assert copyright_template.exists()

    def test_json_report_valid(self, tmp_path: Path):
        report = _make_sample_report()
        findings = [
            _make_finding(
                name="my-ai-model",
                comp_type=ComponentType.AI_MODEL,
                resolved_license="apache-2.0",
            ),
        ]

        pack_dir = generate_compliance_pack(report, findings, tmp_path)
        data = json.loads((pack_dir / "eu_ai_act_report.json").read_text())
        assert data["framework"] == "eu_ai_act"

    def test_html_report_valid(self, tmp_path: Path):
        report = _make_sample_report()
        findings = [
            _make_finding(
                name="my-ai-model",
                comp_type=ComponentType.AI_MODEL,
                resolved_license="apache-2.0",
            ),
        ]

        pack_dir = generate_compliance_pack(report, findings, tmp_path)
        html = (pack_dir / "eu_ai_act_report.html").read_text()
        assert "<!DOCTYPE html>" in html

    def test_training_summary_valid(self, tmp_path: Path):
        report = _make_sample_report()
        findings = [
            _make_finding(
                name="my-ai-model",
                comp_type=ComponentType.AI_MODEL,
                resolved_license="apache-2.0",
                metadata={"datasets": ["wikitext", "c4"]},
            ),
        ]

        pack_dir = generate_compliance_pack(report, findings, tmp_path)
        data = json.loads((pack_dir / "training_data_summary.json").read_text())
        assert data["total_ai_components"] == 1
        assert data["models"][0]["name"] == "my-ai-model"
        assert "wikitext" in data["models"][0]["training_data"]["datasets"]

    def test_copyright_template_content(self, tmp_path: Path):
        report = _make_sample_report()
        findings = [
            _make_finding(
                name="my-ai-model",
                comp_type=ComponentType.AI_MODEL,
                resolved_license="apache-2.0",
            ),
        ]

        pack_dir = generate_compliance_pack(report, findings, tmp_path)
        md = (pack_dir / "copyright_policy_template.md").read_text()
        assert "Copyright Policy" in md
        assert "my-ai-model" in md

    def test_empty_report_compliance_pack(self, tmp_path: Path):
        report = _make_empty_report()
        findings: list[ComponentFinding] = []

        pack_dir = generate_compliance_pack(report, findings, tmp_path)

        assert pack_dir.exists()
        # All 4 files should still be created
        assert (pack_dir / "eu_ai_act_report.json").exists()
        assert (pack_dir / "eu_ai_act_report.html").exists()
        assert (pack_dir / "training_data_summary.json").exists()
        assert (pack_dir / "copyright_policy_template.md").exists()

        # Training data summary should reflect zero components
        data = json.loads((pack_dir / "training_data_summary.json").read_text())
        assert data["total_ai_components"] == 0
        assert data["models"] == []

    def test_mixed_findings_only_ai_in_training_summary(self, tmp_path: Path):
        report = _make_sample_report()
        findings = [
            _make_finding(
                name="requests",
                comp_type=ComponentType.PYTHON,
                resolved_license="Apache-2.0",
            ),
            _make_finding(
                name="my-ai-model",
                comp_type=ComponentType.AI_MODEL,
                resolved_license="apache-2.0",
                metadata={"datasets": ["wikitext"]},
            ),
        ]

        pack_dir = generate_compliance_pack(report, findings, tmp_path)
        data = json.loads((pack_dir / "training_data_summary.json").read_text())
        # Only the AI model should appear in training summary
        assert data["total_ai_components"] == 1
        assert data["models"][0]["name"] == "my-ai-model"
