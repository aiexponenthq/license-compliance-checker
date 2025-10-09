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

"""
Decision recording utilities.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from lcc.config import LCCConfig
from lcc.models import ComponentFinding
from lcc.policy.base import PolicyDecision


@dataclass
class DecisionRecorder:
    """
    Persists policy decisions for auditing purposes.
    """

    config: LCCConfig

    def __post_init__(self) -> None:
        self.path = self.config.decision_log_path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, finding: ComponentFinding, decision: PolicyDecision | dict[str, Any]) -> None:
        metadata = finding.component.metadata if isinstance(finding.component.metadata, dict) else {}
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "component": {
                "name": finding.component.name,
                "type": finding.component.type.value,
                "version": finding.component.version,
            },
            "license": finding.resolved_license or "UNKNOWN",
            "confidence": finding.confidence,
            "decision": decision.to_dict() if isinstance(decision, PolicyDecision) else decision,
            "metadata": metadata,
            "user": os.getenv("LCC_USER") or os.getenv("USER") or os.getenv("USERNAME"),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
