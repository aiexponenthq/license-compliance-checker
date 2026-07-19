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

"""Tests for AI model-card license resolution (finding C4)."""

from __future__ import annotations

import pytest

from lcc.models import Component, ComponentFinding, ComponentType
from lcc.reporting.console_reporter import ConsoleReporter
from lcc.resolution.ai_model import AIModelLicenseResolver


def _model(license_from_card: str | None, **extra) -> Component:
    metadata = {"description": "model"}
    if license_from_card is not None:
        metadata["license_from_card"] = license_from_card
    metadata.update(extra)
    return Component(
        type=ComponentType.AI_MODEL,
        name="test-model",
        version="unknown",
        namespace=None,
        metadata=metadata,
    )


@pytest.fixture
def resolver() -> AIModelLicenseResolver:
    return AIModelLicenseResolver()


@pytest.mark.parametrize(
    "card,expected_expr",
    [
        ("llama3.1", "LicenseRef-llama-3.1"),
        ("llama3", "LicenseRef-llama-3"),
        ("llama2", "LicenseRef-llama-2"),
        ("gemma", "LicenseRef-deepmind-gemma"),
    ],
)
def test_restrictive_ai_licenses_resolved_and_flagged(resolver, card, expected_expr):
    component = _model(card)
    evidences = list(resolver.resolve(component))
    assert len(evidences) == 1
    ev = evidences[0]
    assert ev.license_expression == expected_expr
    assert ev.confidence >= 0.9
    assert component.metadata.get("ai_license_restricted") is True


@pytest.mark.parametrize(
    "card,expected_spdx",
    [("apache-2.0", "Apache-2.0"), ("mit", "MIT"), ("bsd-3-clause", "BSD-3-Clause")],
)
def test_permissive_spdx_licenses_not_flagged(resolver, card, expected_spdx):
    component = _model(card)
    evidences = list(resolver.resolve(component))
    assert len(evidences) == 1
    assert evidences[0].license_expression == expected_spdx
    assert component.metadata.get("ai_license_restricted") is None


def test_other_and_unknown_yield_nothing(resolver):
    assert list(resolver.resolve(_model("other"))) == []
    assert list(resolver.resolve(_model(None))) == []


def test_unrecognised_ai_license_is_flagged_not_assumed_permissive(resolver):
    component = _model("some-custom-model-license")
    evidences = list(resolver.resolve(component))
    assert len(evidences) == 1
    assert evidences[0].license_expression == "LicenseRef-some-custom-model-license"
    assert component.metadata.get("ai_license_restricted") is True


def test_gguf_hint_is_used_when_no_card(resolver):
    component = _model(None, detected_license_hint="llama 3")
    evidences = list(resolver.resolve(component))
    assert evidences[0].license_expression == "LicenseRef-llama-3"


def test_console_reporter_marks_restricted_model_not_pass():
    resolver = AIModelLicenseResolver()
    component = _model("llama3.1")
    finding = ComponentFinding(component=component)
    for ev in resolver.resolve(component):
        finding.evidences.append(ev)
        finding.resolved_license = ev.license_expression
        finding.confidence = ev.confidence
    status, _style = ConsoleReporter()._classify_finding(finding)
    assert status == "RESTRICTED"
