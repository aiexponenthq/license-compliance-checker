"""Tests for lcc.regulatory.eu_ai_act — EU AI Act assessor and helpers."""

from __future__ import annotations

import pytest

from lcc.models import Component, ComponentFinding, ComponentType
from lcc.regulatory.eu_ai_act import (
    EUAIActAssessor,
    get_training_data_info,
    get_use_restrictions,
    is_gpai_model,
)
from lcc.regulatory.frameworks import (
    AIRiskClassification,
    RegulatoryFramework,
)


# ------------------------------------------------------------------ #
#  Test fixtures                                                       #
# ------------------------------------------------------------------ #


def _make_finding(
    name: str = "test-model",
    version: str = "1.0.0",
    comp_type: ComponentType = ComponentType.AI_MODEL,
    resolved_license: str | None = None,
    metadata: dict | None = None,
) -> ComponentFinding:
    """Helper to create a ComponentFinding for testing."""
    return ComponentFinding(
        component=Component(
            type=comp_type,
            name=name,
            version=version,
            metadata=metadata or {},
        ),
        resolved_license=resolved_license,
    )


# ------------------------------------------------------------------ #
#  classify_risk                                                       #
# ------------------------------------------------------------------ #


class TestClassifyRisk:
    def setup_method(self):
        self.assessor = EUAIActAssessor()

    def test_ai_model_with_mit_license_is_gpai(self):
        finding = _make_finding(
            name="my-model",
            comp_type=ComponentType.AI_MODEL,
            resolved_license="MIT",
        )
        assert self.assessor.classify_risk(finding) == AIRiskClassification.GPAI

    def test_ai_model_llama_is_gpai(self):
        finding = _make_finding(
            name="meta-llama/llama-2-7b",
            comp_type=ComponentType.AI_MODEL,
            resolved_license="llama2",
        )
        assert self.assessor.classify_risk(finding) == AIRiskClassification.GPAI

    def test_ai_model_70b_is_gpai_systemic(self):
        finding = _make_finding(
            name="meta-llama/llama-2-70B",
            comp_type=ComponentType.AI_MODEL,
            resolved_license="llama2",
        )
        assert self.assessor.classify_risk(finding) == AIRiskClassification.GPAI_SYSTEMIC

    def test_python_component_is_minimal_risk(self):
        finding = _make_finding(
            name="requests",
            comp_type=ComponentType.PYTHON,
            resolved_license="Apache-2.0",
        )
        assert self.assessor.classify_risk(finding) == AIRiskClassification.MINIMAL_RISK

    def test_ai_model_unknown_license_is_gpai(self):
        finding = _make_finding(
            name="custom-model",
            comp_type=ComponentType.AI_MODEL,
            resolved_license=None,
        )
        assert self.assessor.classify_risk(finding) == AIRiskClassification.GPAI

    def test_dataset_is_gpai(self):
        finding = _make_finding(
            name="common-crawl",
            comp_type=ComponentType.DATASET,
            resolved_license="cc-by-4.0",
        )
        assert self.assessor.classify_risk(finding) == AIRiskClassification.GPAI

    def test_prohibited_use_detected(self):
        finding = _make_finding(
            name="scoring-model",
            comp_type=ComponentType.AI_MODEL,
            metadata={"description": "Model for social scoring of citizens"},
        )
        assert self.assessor.classify_risk(finding) == AIRiskClassification.PROHIBITED

    def test_systemic_risk_175b(self):
        finding = _make_finding(
            name="gpt-175B",
            comp_type=ComponentType.AI_MODEL,
        )
        assert self.assessor.classify_risk(finding) == AIRiskClassification.GPAI_SYSTEMIC

    def test_javascript_component_is_minimal_risk(self):
        finding = _make_finding(
            name="lodash",
            comp_type=ComponentType.JAVASCRIPT,
            resolved_license="MIT",
        )
        assert self.assessor.classify_risk(finding) == AIRiskClassification.MINIMAL_RISK


# ------------------------------------------------------------------ #
#  assess_component                                                    #
# ------------------------------------------------------------------ #


class TestAssessComponent:
    def setup_method(self):
        self.assessor = EUAIActAssessor()

    def test_ai_model_with_full_metadata(self):
        """Model with rich metadata should have mostly 'met' obligations."""
        finding = _make_finding(
            name="my-model",
            version="2.0.0",
            comp_type=ComponentType.AI_MODEL,
            resolved_license="apache-2.0",
            metadata={
                "description": "A language model for text generation.",
                "datasets": ["wikitext", "c4"],
                "training_data_sources": ["Wikipedia"],
                "training_data_description": "Trained on web data.",
                "license_from_card": "apache-2.0",
            },
        )
        assessment = self.assessor.assess_component(finding)

        assert assessment.framework == RegulatoryFramework.EU_AI_ACT
        assert assessment.component_name == "my-model"
        assert assessment.component_type == "ai_model"
        assert assessment.risk_classification == AIRiskClassification.GPAI

        # Check obligations exist
        assert len(assessment.obligations) == 5

        # Technical documentation should be met (name, version, license present)
        tech_doc = assessment.obligations[0]
        assert tech_doc.article == "Art.53(1)(a)"
        assert tech_doc.status == "met"

        # Downstream info should be met (license + description)
        downstream = assessment.obligations[1]
        assert downstream.article == "Art.53(1)(b)"
        assert downstream.status == "met"

        # Copyright policy should be met (apache-2.0 is known open)
        copyright_ob = assessment.obligations[2]
        assert copyright_ob.article == "Art.53(1)(c)"
        assert copyright_ob.status == "met"

        # Training data summary should be met (datasets provided)
        training = assessment.obligations[3]
        assert training.article == "Art.53(1)(d)"
        assert training.status == "met"

        # Systemic risk not applicable for non-systemic
        systemic = assessment.obligations[4]
        assert systemic.article == "Art.53(2)"
        assert systemic.status == "not_applicable"

        # Overall should be compliant
        assert assessment.overall_status == "compliant"

        # assessed_at should be populated
        assert assessment.assessed_at != ""

    def test_ai_model_with_minimal_metadata(self):
        """Model with no metadata should have mostly 'not_met' obligations."""
        finding = _make_finding(
            name="bare-model",
            version="unknown",
            comp_type=ComponentType.AI_MODEL,
            resolved_license=None,
            metadata={},
        )
        assessment = self.assessor.assess_component(finding)

        assert assessment.risk_classification == AIRiskClassification.GPAI
        assert len(assessment.obligations) == 5

        # Technical documentation: no version, no license => not_met
        tech_doc = assessment.obligations[0]
        assert tech_doc.status == "not_met"

        # Downstream info: no license, no description => not_met
        downstream = assessment.obligations[1]
        assert downstream.status == "not_met"

        # Copyright policy: no license => not_met
        copyright_ob = assessment.obligations[2]
        assert copyright_ob.status == "not_met"

        # Training data: no data => not_met
        training = assessment.obligations[3]
        assert training.status == "not_met"

        # Overall should be non_compliant
        assert assessment.overall_status == "non_compliant"

        # Should have recommendations for unmet obligations
        assert len(assessment.recommendations) > 0

    def test_dataset_component(self):
        """Dataset component should be assessed as GPAI."""
        finding = _make_finding(
            name="openwebtext",
            version="1.0",
            comp_type=ComponentType.DATASET,
            resolved_license="cc-by-4.0",
            metadata={
                "description": "Open reproduction of WebText dataset.",
            },
        )
        assessment = self.assessor.assess_component(finding)

        assert assessment.component_type == "dataset"
        assert assessment.risk_classification == AIRiskClassification.GPAI

        # License resolved, so tech doc should be met
        assert assessment.obligations[0].status == "met"

    def test_assessment_to_dict(self):
        """Assessment serialises correctly."""
        finding = _make_finding(
            name="test-model",
            comp_type=ComponentType.AI_MODEL,
            resolved_license="MIT",
        )
        assessment = self.assessor.assess_component(finding)
        d = assessment.to_dict()

        assert isinstance(d, dict)
        assert d["framework"] == "eu_ai_act"
        assert d["component_name"] == "test-model"
        assert isinstance(d["obligations"], list)


# ------------------------------------------------------------------ #
#  assess_scan                                                         #
# ------------------------------------------------------------------ #


class TestAssessScan:
    def setup_method(self):
        self.assessor = EUAIActAssessor()

    def test_mixed_findings_only_ai_assessed(self):
        """Only AI_MODEL and DATASET components should be assessed."""
        findings = [
            _make_finding(
                name="requests",
                comp_type=ComponentType.PYTHON,
                resolved_license="Apache-2.0",
            ),
            _make_finding(
                name="my-ai-model",
                comp_type=ComponentType.AI_MODEL,
                resolved_license="MIT",
            ),
            _make_finding(
                name="lodash",
                comp_type=ComponentType.JAVASCRIPT,
                resolved_license="MIT",
            ),
            _make_finding(
                name="training-set",
                comp_type=ComponentType.DATASET,
                resolved_license="cc-by-4.0",
            ),
        ]
        report = self.assessor.assess_scan(findings)

        assert report.title == "EU AI Act Article 53 GPAI Compliance Report"
        assert report.framework == RegulatoryFramework.EU_AI_ACT
        assert report.generated_at != ""

        # Only AI model and dataset should be assessed
        assert len(report.assessments) == 2
        names = {a.component_name for a in report.assessments}
        assert "my-ai-model" in names
        assert "training-set" in names
        assert "requests" not in names
        assert "lodash" not in names

        # Summary should reflect counts
        assert report.summary["total_ai_components"] == 2

    def test_empty_findings(self):
        """Empty findings should produce an empty report."""
        report = self.assessor.assess_scan([])

        assert len(report.assessments) == 0
        assert report.summary["total_ai_components"] == 0
        assert report.summary["compliance_percentage"] == 0.0

    def test_only_non_ai_findings(self):
        """Non-AI findings should result in zero assessments."""
        findings = [
            _make_finding(
                name="flask",
                comp_type=ComponentType.PYTHON,
                resolved_license="BSD-3-Clause",
            ),
        ]
        report = self.assessor.assess_scan(findings)
        assert len(report.assessments) == 0
        assert report.summary["total_ai_components"] == 0

    def test_report_to_dict(self):
        """Report serialises correctly."""
        findings = [
            _make_finding(
                name="test-model",
                comp_type=ComponentType.AI_MODEL,
                resolved_license="MIT",
            ),
        ]
        report = self.assessor.assess_scan(findings)
        d = report.to_dict()

        assert isinstance(d, dict)
        assert d["framework"] == "eu_ai_act"
        assert isinstance(d["assessments"], list)
        assert isinstance(d["summary"], dict)


# ------------------------------------------------------------------ #
#  Helper functions                                                    #
# ------------------------------------------------------------------ #


class TestGetUseRestrictions:
    def test_no_restrictions(self):
        finding = _make_finding(
            name="basic-model",
            comp_type=ComponentType.AI_MODEL,
            resolved_license="MIT",
        )
        restrictions = get_use_restrictions(finding)
        # MIT has no use restrictions in the AI license registry
        assert isinstance(restrictions, list)

    def test_restrictions_from_metadata(self):
        finding = _make_finding(
            name="restricted-model",
            comp_type=ComponentType.AI_MODEL,
            metadata={"use_restrictions": ["no-harm", "no-illegal-activity"]},
        )
        restrictions = get_use_restrictions(finding)
        assert "no-harm" in restrictions
        assert "no-illegal-activity" in restrictions

    def test_empty_metadata(self):
        finding = _make_finding(
            name="model",
            comp_type=ComponentType.AI_MODEL,
            metadata={},
        )
        restrictions = get_use_restrictions(finding)
        assert isinstance(restrictions, list)


class TestIsGPAIModel:
    def test_ai_model_is_gpai(self):
        finding = _make_finding(comp_type=ComponentType.AI_MODEL)
        assert is_gpai_model(finding) is True

    def test_dataset_is_gpai(self):
        finding = _make_finding(comp_type=ComponentType.DATASET)
        assert is_gpai_model(finding) is True

    def test_python_is_not_gpai(self):
        finding = _make_finding(comp_type=ComponentType.PYTHON)
        assert is_gpai_model(finding) is False

    def test_javascript_is_not_gpai(self):
        finding = _make_finding(comp_type=ComponentType.JAVASCRIPT)
        assert is_gpai_model(finding) is False

    def test_generic_is_not_gpai(self):
        finding = _make_finding(comp_type=ComponentType.GENERIC)
        assert is_gpai_model(finding) is False


class TestGetTrainingDataInfo:
    def test_with_datasets(self):
        finding = _make_finding(
            metadata={"datasets": ["wikitext", "c4"]},
        )
        info = get_training_data_info(finding)
        assert info["datasets"] == ["wikitext", "c4"]
        assert info["sources"] == []
        assert info["description"] is None

    def test_with_sources_and_description(self):
        finding = _make_finding(
            metadata={
                "training_data_sources": ["Wikipedia", "CommonCrawl"],
                "training_data_description": "Trained on web data.",
            },
        )
        info = get_training_data_info(finding)
        assert info["sources"] == ["Wikipedia", "CommonCrawl"]
        assert info["description"] == "Trained on web data."

    def test_empty_metadata(self):
        finding = _make_finding(metadata={})
        info = get_training_data_info(finding)
        assert info["datasets"] == []
        assert info["sources"] == []
        assert info["description"] is None

    def test_string_datasets_coerced_to_list(self):
        finding = _make_finding(
            metadata={"datasets": "single-dataset"},
        )
        info = get_training_data_info(finding)
        assert info["datasets"] == ["single-dataset"]

    def test_string_sources_coerced_to_list(self):
        finding = _make_finding(
            metadata={"training_data_sources": "Wikipedia"},
        )
        info = get_training_data_info(finding)
        assert info["sources"] == ["Wikipedia"]
