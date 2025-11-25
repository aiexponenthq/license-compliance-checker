"""
OPA policy evaluation client.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Optional

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
        policy_name: Optional[str] = None,
        *,
        context: Optional[str] = None,
        licenses: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate a component finding against OPA, returning the decision document.
        """

        url = f"{self.base_url}/v1/data/lcc/license/decision"
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        license_options = list(licenses) if licenses else None
        payload: Dict[str, Any] = {
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
