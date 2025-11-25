"""
Decision recording utilities.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Union

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

    def record(self, finding: ComponentFinding, decision: Union[PolicyDecision, Dict[str, Any]]) -> None:
        metadata = finding.component.metadata if isinstance(finding.component.metadata, dict) else {}
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
