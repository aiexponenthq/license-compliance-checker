"""Tests for lcc.regulatory.frameworks — enums and dataclasses."""

from __future__ import annotations

import pytest

from lcc.regulatory.frameworks import (
    AIRiskClassification,
    Article53Obligation,
    CopyrightComplianceStatus,
    RegulatoryAssessment,
    RegulatoryFramework,
    RegulatoryMetadata,
    RegulatoryReport,
    TransparencyRequirement,
)


# ------------------------------------------------------------------ #
#  Enum value existence                                                #
# ------------------------------------------------------------------ #


class TestRegulatoryFrameworkEnum:
    """RegulatoryFramework enum has all expected members."""

    def test_eu_ai_act(self):
        assert RegulatoryFramework.EU_AI_ACT == "eu_ai_act"

    def test_nist_ai_rmf(self):
        assert RegulatoryFramework.NIST_AI_RMF == "nist_ai_rmf"

    def test_iso_42001(self):
        assert RegulatoryFramework.ISO_42001 == "iso_42001"

    def test_us_eo_14110(self):
        assert RegulatoryFramework.US_EO_14110 == "us_eo_14110"

    def test_member_count(self):
        assert len(RegulatoryFramework) == 4

    def test_str_enum_behaviour(self):
        """Values should be usable as plain strings (StrEnum)."""
        assert isinstance(RegulatoryFramework.EU_AI_ACT, str)
        assert str(RegulatoryFramework.EU_AI_ACT) == "eu_ai_act"


class TestAIRiskClassificationEnum:
    """AIRiskClassification enum has all expected members."""

    def test_prohibited(self):
        assert AIRiskClassification.PROHIBITED == "prohibited"

    def test_high_risk(self):
        assert AIRiskClassification.HIGH_RISK == "high_risk"

    def test_limited_risk(self):
        assert AIRiskClassification.LIMITED_RISK == "limited_risk"

    def test_minimal_risk(self):
        assert AIRiskClassification.MINIMAL_RISK == "minimal_risk"

    def test_gpai(self):
        assert AIRiskClassification.GPAI == "general_purpose_ai"

    def test_gpai_systemic(self):
        assert AIRiskClassification.GPAI_SYSTEMIC == "gpai_systemic_risk"

    def test_member_count(self):
        assert len(AIRiskClassification) == 6

    def test_str_enum_behaviour(self):
        assert isinstance(AIRiskClassification.GPAI, str)


class TestCopyrightComplianceStatusEnum:
    def test_verified(self):
        assert CopyrightComplianceStatus.VERIFIED == "verified"

    def test_unverified(self):
        assert CopyrightComplianceStatus.UNVERIFIED == "unverified"

    def test_mixed(self):
        assert CopyrightComplianceStatus.MIXED == "mixed"

    def test_unknown(self):
        assert CopyrightComplianceStatus.UNKNOWN == "unknown"

    def test_member_count(self):
        assert len(CopyrightComplianceStatus) == 4

    def test_str_enum_behaviour(self):
        assert isinstance(CopyrightComplianceStatus.VERIFIED, str)


class TestTransparencyRequirementEnum:
    def test_model_card(self):
        assert TransparencyRequirement.MODEL_CARD == "model_card"

    def test_training_data_summary(self):
        assert TransparencyRequirement.TRAINING_DATA_SUMMARY == "training_data_summary"

    def test_copyright_policy(self):
        assert TransparencyRequirement.COPYRIGHT_POLICY == "copyright_policy"

    def test_technical_documentation(self):
        assert TransparencyRequirement.TECHNICAL_DOCUMENTATION == "technical_documentation"

    def test_sbom(self):
        assert TransparencyRequirement.SBOM == "sbom"

    def test_member_count(self):
        assert len(TransparencyRequirement) == 5

    def test_str_enum_behaviour(self):
        assert isinstance(TransparencyRequirement.SBOM, str)


# ------------------------------------------------------------------ #
#  RegulatoryMetadata dataclass                                        #
# ------------------------------------------------------------------ #


class TestRegulatoryMetadata:
    def test_defaults(self):
        """Creating with no args should give sensible defaults."""
        meta = RegulatoryMetadata()
        assert meta.risk_classification is None
        assert meta.applicable_articles == []
        assert meta.transparency_requirements == []
        assert meta.copyright_compliance == CopyrightComplianceStatus.UNKNOWN
        assert meta.training_data_sources == []
        assert meta.training_data_licenses == []
        assert meta.training_data_summary is None
        assert meta.use_restrictions == []
        assert meta.known_limitations is None
        assert meta.evaluation_metrics == {}
        assert meta.environmental_impact is None
        assert meta.frameworks == []
        assert meta.compliance_gaps == []
        assert meta.compliance_score is None

    def test_creation_with_values(self):
        meta = RegulatoryMetadata(
            risk_classification=AIRiskClassification.GPAI,
            applicable_articles=["Art.53(1)(a)"],
            transparency_requirements=[TransparencyRequirement.MODEL_CARD],
            copyright_compliance=CopyrightComplianceStatus.VERIFIED,
            frameworks=[RegulatoryFramework.EU_AI_ACT],
            compliance_score=0.85,
        )
        assert meta.risk_classification == AIRiskClassification.GPAI
        assert meta.applicable_articles == ["Art.53(1)(a)"]
        assert meta.transparency_requirements == [TransparencyRequirement.MODEL_CARD]
        assert meta.copyright_compliance == CopyrightComplianceStatus.VERIFIED
        assert meta.frameworks == [RegulatoryFramework.EU_AI_ACT]
        assert meta.compliance_score == 0.85

    def test_to_dict_defaults(self):
        meta = RegulatoryMetadata()
        d = meta.to_dict()
        assert isinstance(d, dict)
        assert d["risk_classification"] is None
        assert d["copyright_compliance"] == "unknown"
        assert d["transparency_requirements"] == []
        assert d["frameworks"] == []

    def test_to_dict_with_values(self):
        meta = RegulatoryMetadata(
            risk_classification=AIRiskClassification.GPAI,
            transparency_requirements=[
                TransparencyRequirement.MODEL_CARD,
                TransparencyRequirement.SBOM,
            ],
            copyright_compliance=CopyrightComplianceStatus.VERIFIED,
            frameworks=[RegulatoryFramework.EU_AI_ACT, RegulatoryFramework.NIST_AI_RMF],
        )
        d = meta.to_dict()
        assert d["risk_classification"] == "general_purpose_ai"
        assert d["copyright_compliance"] == "verified"
        assert d["transparency_requirements"] == ["model_card", "sbom"]
        assert d["frameworks"] == ["eu_ai_act", "nist_ai_rmf"]


# ------------------------------------------------------------------ #
#  Article53Obligation dataclass                                       #
# ------------------------------------------------------------------ #


class TestArticle53Obligation:
    def test_creation_with_defaults(self):
        ob = Article53Obligation(
            article="Art.53(1)(a)",
            title="Technical documentation",
            description="Draw up and keep up-to-date the technical documentation.",
        )
        assert ob.article == "Art.53(1)(a)"
        assert ob.title == "Technical documentation"
        assert ob.status == "not_met"
        assert ob.evidence == []
        assert ob.gaps == []

    def test_creation_with_values(self):
        ob = Article53Obligation(
            article="Art.53(1)(b)",
            title="Info for downstream providers",
            description="Provide info.",
            status="met",
            evidence=["License resolved: MIT"],
            gaps=[],
        )
        assert ob.status == "met"
        assert ob.evidence == ["License resolved: MIT"]

    def test_to_dict(self):
        ob = Article53Obligation(
            article="Art.53(1)(c)",
            title="Copyright policy",
            description="Put in place a policy.",
            status="partial",
            evidence=["License: Apache-2.0"],
            gaps=["Use restrictions present"],
        )
        d = ob.to_dict()
        assert isinstance(d, dict)
        assert d["article"] == "Art.53(1)(c)"
        assert d["title"] == "Copyright policy"
        assert d["status"] == "partial"
        assert d["evidence"] == ["License: Apache-2.0"]
        assert d["gaps"] == ["Use restrictions present"]


# ------------------------------------------------------------------ #
#  RegulatoryAssessment dataclass                                      #
# ------------------------------------------------------------------ #


class TestRegulatoryAssessment:
    def test_creation_with_defaults(self):
        ra = RegulatoryAssessment(
            framework=RegulatoryFramework.EU_AI_ACT,
            component_name="test-model",
            component_type="ai_model",
        )
        assert ra.framework == RegulatoryFramework.EU_AI_ACT
        assert ra.component_name == "test-model"
        assert ra.component_type == "ai_model"
        assert ra.risk_classification is None
        assert ra.obligations == []
        assert ra.overall_status == "non_compliant"
        assert ra.recommendations == []
        assert ra.assessed_at == ""

    def test_creation_with_all_fields(self):
        ob = Article53Obligation(
            article="Art.53(1)(a)",
            title="Technical documentation",
            description="Test",
            status="met",
        )
        ra = RegulatoryAssessment(
            framework=RegulatoryFramework.EU_AI_ACT,
            component_name="llama-7b",
            component_type="ai_model",
            risk_classification=AIRiskClassification.GPAI,
            obligations=[ob],
            overall_status="compliant",
            recommendations=["Check documentation"],
            assessed_at="2025-01-01T00:00:00",
        )
        assert ra.risk_classification == AIRiskClassification.GPAI
        assert len(ra.obligations) == 1
        assert ra.overall_status == "compliant"

    def test_to_dict(self):
        ob = Article53Obligation(
            article="Art.53(1)(a)",
            title="Tech docs",
            description="Desc",
            status="met",
        )
        ra = RegulatoryAssessment(
            framework=RegulatoryFramework.EU_AI_ACT,
            component_name="test-model",
            component_type="ai_model",
            risk_classification=AIRiskClassification.GPAI_SYSTEMIC,
            obligations=[ob],
            overall_status="partial",
            recommendations=["Fix X"],
            assessed_at="2025-01-01T00:00:00",
        )
        d = ra.to_dict()
        assert d["framework"] == "eu_ai_act"
        assert d["component_name"] == "test-model"
        assert d["risk_classification"] == "gpai_systemic_risk"
        assert len(d["obligations"]) == 1
        assert d["obligations"][0]["status"] == "met"
        assert d["overall_status"] == "partial"
        assert d["recommendations"] == ["Fix X"]

    def test_to_dict_none_risk(self):
        ra = RegulatoryAssessment(
            framework=RegulatoryFramework.EU_AI_ACT,
            component_name="test",
            component_type="python",
        )
        d = ra.to_dict()
        assert d["risk_classification"] is None


# ------------------------------------------------------------------ #
#  RegulatoryReport dataclass                                          #
# ------------------------------------------------------------------ #


class TestRegulatoryReport:
    def test_creation_with_defaults(self):
        report = RegulatoryReport(
            title="Test Report",
            framework=RegulatoryFramework.EU_AI_ACT,
        )
        assert report.title == "Test Report"
        assert report.framework == RegulatoryFramework.EU_AI_ACT
        assert report.generated_at == ""
        assert report.assessments == []
        assert report.summary == {}

    def test_to_dict(self):
        ob = Article53Obligation(
            article="Art.53(1)(a)",
            title="Tech docs",
            description="Desc",
            status="met",
        )
        assessment = RegulatoryAssessment(
            framework=RegulatoryFramework.EU_AI_ACT,
            component_name="model-x",
            component_type="ai_model",
            risk_classification=AIRiskClassification.GPAI,
            obligations=[ob],
            overall_status="compliant",
        )
        report = RegulatoryReport(
            title="Test Report",
            framework=RegulatoryFramework.EU_AI_ACT,
            generated_at="2025-06-01T12:00:00",
            assessments=[assessment],
            summary={"total": 1, "compliant": 1},
        )
        d = report.to_dict()
        assert d["title"] == "Test Report"
        assert d["framework"] == "eu_ai_act"
        assert d["generated_at"] == "2025-06-01T12:00:00"
        assert len(d["assessments"]) == 1
        assert d["summary"]["total"] == 1

    def test_to_dict_empty(self):
        report = RegulatoryReport(
            title="Empty",
            framework=RegulatoryFramework.NIST_AI_RMF,
        )
        d = report.to_dict()
        assert d["assessments"] == []
        assert d["summary"] == {}
