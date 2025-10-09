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
OPA policy evaluation client.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

import requests

from lcc.config import LCCConfig
from lcc.models import ComponentFinding


class OPAClientError(RuntimeError):
    """Raised when OPA evaluation fails."""


class OPAClient:
    """
    Lightweight client for communicating with an OPA policy server.
    """

    def __init__(self, config: LCCConfig) -> None:
        if not config.opa_url:
            raise ValueError("OPA URL must be configured to use OPAClient.")
        self.base_url = config.opa_url.rstrip("/")
        self.token = config.opa_token
        self.timeout = float(config.timeouts.get("opa", config.timeouts.get("default", 10.0)))

    def evaluate(
        self,
        finding: ComponentFinding,
        policy_name: str | None = None,
        *,
        context: str | None = None,
        licenses: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """
        Evaluate a component finding against OPA, returning the decision document.
        """

        url = f"{self.base_url}/v1/data/lcc/license/decision"
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        license_options = list(licenses) if licenses else None
        payload: dict[str, Any] = {
            "input": {
                "component": {
                    "name": finding.component.name,
                    "type": finding.component.type.value,
                    "version": finding.component.version,
                    "metadata": finding.component.metadata,
                },
                "license": finding.resolved_license or "UNKNOWN",
                "confidence": finding.confidence,
                "policy": policy_name or "",
            }
        }
        if context:
            payload["input"]["context"] = context
        if license_options:
            payload["input"]["license_options"] = license_options
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=self.timeout)
        except requests.RequestException as exc:  # pragma: no cover - network dependent
            raise OPAClientError(f"OPA request failed: {exc}") from exc

        if response.status_code >= 400:
            raise OPAClientError(f"OPA returned {response.status_code}: {response.text}")

        try:
            body = response.json()
        except ValueError as exc:
            raise OPAClientError(f"Invalid JSON response from OPA: {exc}") from exc

        result = body.get("result", {})
        if not isinstance(result, dict):
            raise OPAClientError("OPA response missing decision result.")
        return result
