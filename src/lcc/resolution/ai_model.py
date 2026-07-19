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

"""Resolver that turns an AI model card license into license evidence.

The HuggingFace detectors record a model's declared license in
``component.metadata["license_from_card"]`` (and GGUF metadata in
``detected_license_hint``), but nothing converted it into evidence, so a model
with a clearly declared restrictive license (Llama, Gemma, OpenRAIL, ...)
resolved to UNKNOWN and could be overridden by an incidental permissive file
license. This resolver attributes the declared license at high confidence and
marks restrictive AI licenses so they are never reported as a silent pass.
"""

from __future__ import annotations

from collections.abc import Iterable

from lcc.ai.licenses import get_ai_license_info
from lcc.models import Component, LicenseEvidence
from lcc.resolution.base import Resolver

# Model-card license strings (and GGUF hints) map to AI_LICENSES registry keys.
_AI_LICENSE_ALIASES = {
    "llama2": "llama-2",
    "llama-2": "llama-2",
    "llama 2": "llama-2",
    "llama3": "llama-3",
    "llama-3": "llama-3",
    "llama 3": "llama-3",
    "llama3.1": "llama-3.1",
    "llama-3.1": "llama-3.1",
    "llama 3.1": "llama-3.1",
    "gemma": "deepmind-gemma",
    "mistral": "mistral-ai",
    "mistral-ai": "mistral-ai",
    "openrail": "openrail",
    "openrail-m": "openrail-m",
    "creativeml-openrail-m": "creativeml-openrail-m",
    "bigscience-bloom-rail-1.0": "bigscience-bloom-rail-1.0",
    "bigscience-openrail-m": "bigscience-openrail-m",
    "cohere": "cohere",
    "anthropic-claude": "anthropic-claude",
    "openai-gpt": "openai-gpt",
    "ai21-jurassic": "ai21-jurassic",
}

# Standard SPDX licenses that a model card may declare directly. These are
# attributed verbatim and are not marked restrictive here (policy handles them).
_SPDX_LICENSES = {
    "apache-2.0": "Apache-2.0",
    "apache2.0": "Apache-2.0",
    "apache 2.0": "Apache-2.0",
    "mit": "MIT",
    "bsd-3-clause": "BSD-3-Clause",
    "bsd-2-clause": "BSD-2-Clause",
    "gpl-3.0": "GPL-3.0-only",
    "gpl-2.0": "GPL-2.0-only",
    "lgpl-3.0": "LGPL-3.0-only",
    "isc": "ISC",
    "unlicense": "Unlicense",
    "cc0-1.0": "CC0-1.0",
    "cc-by-4.0": "CC-BY-4.0",
    "cc-by-sa-4.0": "CC-BY-SA-4.0",
}

_UNRESOLVABLE = {"", "other", "unknown", "unlicensed", "none"}


def _is_restrictive(info) -> bool:
    """A registry license is restrictive if it carries use restrictions, forbids
    commercial use, or is not a purely permissive category."""
    return (
        bool(info.use_restrictions)
        or not info.commercial_use
        or "permissive" not in (info.category or "").lower()
    )


class AIModelLicenseResolver(Resolver):
    """Attribute an AI model/dataset license from its declared card metadata."""

    def __init__(self) -> None:
        super().__init__(name="ai-model-card")

    def resolve(self, component: Component) -> Iterable[LicenseEvidence]:
        metadata = component.metadata if isinstance(component.metadata, dict) else {}
        raw = metadata.get("license_from_card") or metadata.get("detected_license_hint")
        if not raw or not isinstance(raw, str):
            return

        key = raw.strip().lower()
        if key in _UNRESOLVABLE:
            return

        spdx = _SPDX_LICENSES.get(key)
        if spdx:
            yield LicenseEvidence(
                source="ai-model-card",
                license_expression=spdx,
                confidence=0.95,
                raw_data={"raw_license": raw},
            )
            return

        info = get_ai_license_info(_AI_LICENSE_ALIASES.get(key, key))
        if info is None:
            # Unrecognised license string: attribute it verbatim so it is not
            # lost, and mark it restrictive because an unrecognised AI license
            # must not be assumed permissive.
            metadata["ai_license_restricted"] = True
            metadata["ai_license_name"] = raw.strip()
            component.metadata = metadata
            yield LicenseEvidence(
                source="ai-model-card",
                license_expression=f"LicenseRef-{raw.strip()}",
                confidence=0.9,
                raw_data={"raw_license": raw, "restricted": True},
            )
            return

        restricted = _is_restrictive(info)
        if restricted:
            metadata["ai_license_restricted"] = True
            metadata["ai_license_name"] = info.name
            metadata["ai_license_restrictions"] = info.use_restrictions
            component.metadata = metadata

        yield LicenseEvidence(
            source="ai-model-card",
            license_expression=info.spdx_id or f"LicenseRef-{info.id}",
            confidence=0.95,
            url=info.url,
            raw_data={"raw_license": raw, "restricted": restricted},
        )
