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

"""Tests for SBOM regulatory properties helper."""

from __future__ import annotations

import pytest

from lcc.models import (
    Component,
    ComponentResult,
    ComponentType,
    LicenseEvidence,
    Status,
)
from lcc.sbom.regulatory_properties import (
    get_regulatory_annotation_text,
    get_regulatory_properties,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ai_model_component() -> Component:
    """An AI_MODEL component with training-data and restriction metadata."""
    return Component(
        type=ComponentType.AI_MODEL,
        name="llama-2-7b",
        version="2.0",
        namespace=None,
        metadata={
            "training_data_sources": ["Common Crawl", "Wikipedia", "Books3"],
            "use_restrictions": ["no-military", "no-surveillance"],
            "copyright_compliance": "documented",
        },
    )


@pytest.fixture
def dataset_component() -> Component:
    """A DATASET component."""
    return Component(
        type=ComponentType.DATASET,
        name="imagenet",
        version="2012",
        namespace=None,
        metadata={
            "datasets": ["ImageNet-1k"],
        },
    )


@pytest.fixture
def python_component() -> Component:
    """A plain PYTHON library component."""
    return Component(
        type=ComponentType.PYTHON,
        name="requests",
        version="2.31.0",
    )


def _make_result(component: Component, license_expr: str, confidence: float = 0.95) -> ComponentResult:
    """Helper to build a ComponentResult with a single licence evidence."""
    return ComponentResult(
        component=component,
        status=Status.PASS,
        licenses=[
            LicenseEvidence(
                source="test",
                license_expression=license_expr,
                confidence=confidence,
            )
        ],
    )


# ---------------------------------------------------------------------------
# Tests: get_regulatory_properties()
# ---------------------------------------------------------------------------


class TestGetRegulatoryProperties:
    """Tests for get_regulatory_properties()."""

    def test_ai_model_returns_seven_properties(self, ai_model_component: Component) -> None:
        """AI_MODEL component should yield exactly 7 regulatory properties."""
        props = get_regulatory_properties(ai_model_component)
        assert len(props) == 7

    def test_python_component_returns_empty(self, python_component: Component) -> None:
        """Non-AI component should yield an empty dict."""
        props = get_regulatory_properties(python_component)
        assert props == {}

    def test_dataset_component_returns_properties(self, dataset_component: Component) -> None:
        """DATASET component is also AI-adjacent and should produce properties."""
        props = get_regulatory_properties(dataset_component)
        assert len(props) == 7

    def test_property_keys_all_prefixed(self, ai_model_component: Component) -> None:
        """All property keys must start with 'lcc:regulatory:'."""
        props = get_regulatory_properties(ai_model_component)
        expected_keys = {
            "lcc:regulatory:framework",
            "lcc:regulatory:risk_classification",
            "lcc:regulatory:copyright_compliance",
            "lcc:regulatory:training_data_sources",
            "lcc:regulatory:use_restrictions",
            "lcc:regulatory:eu_ai_act_article_53",
            "lcc:regulatory:transparency_required",
        }
        assert set(props.keys()) == expected_keys

    # -- Risk classification ------------------------------------------------

    def test_risk_classification_mit_is_minimal(self, ai_model_component: Component) -> None:
        """MIT licence should map to 'minimal_risk'."""
        result = _make_result(ai_model_component, "MIT")
        props = get_regulatory_properties(ai_model_component, result)
        assert props["lcc:regulatory:risk_classification"] == "minimal_risk"

    def test_risk_classification_rail_is_general_purpose(self, ai_model_component: Component) -> None:
        """A RAIL licence pattern should map to 'general_purpose_ai'."""
        result = _make_result(ai_model_component, "OpenRAIL-M")
        props = get_regulatory_properties(ai_model_component, result)
        assert props["lcc:regulatory:risk_classification"] == "general_purpose_ai"

    def test_risk_classification_unknown_licence(self, ai_model_component: Component) -> None:
        """An unrecognised licence string should map to 'unknown'."""
        result = _make_result(ai_model_component, "SomeObscureLicense-1.0")
        props = get_regulatory_properties(ai_model_component, result)
        assert props["lcc:regulatory:risk_classification"] == "unknown"

    def test_risk_classification_no_result(self, ai_model_component: Component) -> None:
        """No component result at all should yield 'unknown' classification."""
        props = get_regulatory_properties(ai_model_component, None)
        assert props["lcc:regulatory:risk_classification"] == "unknown"

    def test_risk_classification_gpl_is_general_purpose(self, ai_model_component: Component) -> None:
        """GPL licence pattern should be caught by _RAIL_LICENSE_PATTERNS."""
        result = _make_result(ai_model_component, "GPL-3.0")
        props = get_regulatory_properties(ai_model_component, result)
        assert props["lcc:regulatory:risk_classification"] == "general_purpose_ai"

    # -- Metadata extraction -------------------------------------------------

    def test_training_data_sources_from_metadata(self, ai_model_component: Component) -> None:
        """Training data sources should be populated from component metadata."""
        props = get_regulatory_properties(ai_model_component)
        value = props["lcc:regulatory:training_data_sources"]
        assert "Common Crawl" in value
        assert "Wikipedia" in value
        assert "Books3" in value

    def test_training_data_sources_from_datasets_key(self, dataset_component: Component) -> None:
        """'datasets' metadata key should also feed training_data_sources."""
        props = get_regulatory_properties(dataset_component)
        assert "ImageNet-1k" in props["lcc:regulatory:training_data_sources"]

    def test_training_data_sources_unknown_when_absent(self) -> None:
        """When no training data metadata is present, value should be 'unknown'."""
        component = Component(
            type=ComponentType.AI_MODEL,
            name="bare-model",
            version="1.0",
            metadata={},
        )
        props = get_regulatory_properties(component)
        assert props["lcc:regulatory:training_data_sources"] == "unknown"

    def test_use_restrictions_from_metadata(self, ai_model_component: Component) -> None:
        """Use restrictions should be populated from component metadata."""
        props = get_regulatory_properties(ai_model_component)
        value = props["lcc:regulatory:use_restrictions"]
        assert "no-military" in value
        assert "no-surveillance" in value

    def test_use_restrictions_none_when_absent(self) -> None:
        """When no use_restrictions metadata, value should be 'none'."""
        component = Component(
            type=ComponentType.AI_MODEL,
            name="bare-model",
            version="1.0",
            metadata={},
        )
        props = get_regulatory_properties(component)
        assert props["lcc:regulatory:use_restrictions"] == "none"

    def test_copyright_compliance_from_metadata(self, ai_model_component: Component) -> None:
        """Copyright compliance value should come from component metadata."""
        props = get_regulatory_properties(ai_model_component)
        assert props["lcc:regulatory:copyright_compliance"] == "documented"

    def test_copyright_compliance_unknown_when_absent(self) -> None:
        """Missing copyright_compliance metadata should default to 'unknown'."""
        component = Component(
            type=ComponentType.AI_MODEL,
            name="bare-model",
            version="1.0",
            metadata={},
        )
        props = get_regulatory_properties(component)
        assert props["lcc:regulatory:copyright_compliance"] == "unknown"

    # -- Article 53 / Transparency -----------------------------------------

    def test_article_53_applicable_for_general_purpose(self, ai_model_component: Component) -> None:
        """general_purpose_ai risk should trigger Article 53 applicability."""
        result = _make_result(ai_model_component, "AGPL-3.0")
        props = get_regulatory_properties(ai_model_component, result)
        assert props["lcc:regulatory:eu_ai_act_article_53"] == "applicable"

    def test_article_53_not_applicable_for_minimal_risk(self, ai_model_component: Component) -> None:
        """minimal_risk classification should NOT trigger Article 53."""
        result = _make_result(ai_model_component, "MIT")
        props = get_regulatory_properties(ai_model_component, result)
        assert props["lcc:regulatory:eu_ai_act_article_53"] == "not_applicable"

    def test_transparency_required_for_general_purpose(self, ai_model_component: Component) -> None:
        """general_purpose_ai risk should require transparency."""
        result = _make_result(ai_model_component, "AGPL-3.0")
        props = get_regulatory_properties(ai_model_component, result)
        assert props["lcc:regulatory:transparency_required"] == "true"

    def test_transparency_not_required_for_minimal_risk(self, ai_model_component: Component) -> None:
        """minimal_risk classification should NOT require transparency."""
        result = _make_result(ai_model_component, "MIT")
        props = get_regulatory_properties(ai_model_component, result)
        assert props["lcc:regulatory:transparency_required"] == "false"


# ---------------------------------------------------------------------------
# Tests: get_regulatory_annotation_text()
# ---------------------------------------------------------------------------


class TestGetRegulatoryAnnotationText:
    """Tests for get_regulatory_annotation_text()."""

    def test_returns_text_for_ai_model(self, ai_model_component: Component) -> None:
        """Should return annotation text string for AI_MODEL component."""
        text = get_regulatory_annotation_text(ai_model_component)
        assert text is not None
        assert isinstance(text, str)
        assert "LCC Regulatory Metadata" in text
        assert "Risk classification" in text

    def test_returns_none_for_non_ai(self, python_component: Component) -> None:
        """Should return None for a non-AI component."""
        text = get_regulatory_annotation_text(python_component)
        assert text is None

    def test_annotation_contains_metadata_values(self, ai_model_component: Component) -> None:
        """Annotation text should reflect the component metadata."""
        result = _make_result(ai_model_component, "MIT")
        text = get_regulatory_annotation_text(ai_model_component, result)
        assert text is not None
        assert "minimal_risk" in text
        assert "documented" in text  # copyright_compliance
        assert "Common Crawl" in text
        assert "no-military" in text

    def test_annotation_for_dataset(self, dataset_component: Component) -> None:
        """DATASET components should also get annotation text."""
        text = get_regulatory_annotation_text(dataset_component)
        assert text is not None
        assert "LCC Regulatory Metadata" in text
