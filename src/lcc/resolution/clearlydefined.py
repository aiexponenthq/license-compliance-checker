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
ClearlyDefined resolver implementation.
"""

from __future__ import annotations

from collections.abc import Iterable

import requests

from lcc.cache import Cache
from lcc.config import LCCConfig
from lcc.models import Component, ComponentType, LicenseEvidence
from lcc.resolution.base import Resolver


class ClearlyDefinedResolver(Resolver):
    """
    Fetches license information from ClearlyDefined API.
    """

    BASE_URL = "https://api.clearlydefined.io/definitions"

    def __init__(self, cache: Cache, config: LCCConfig) -> None:
        super().__init__(name="clearlydefined")
        self.cache = cache
        self.config = config

    def resolve(self, component: Component) -> Iterable[LicenseEvidence]:
        if getattr(self.config, "offline", False):
            return []
        coordinate = self._build_coordinate(component)
        if not coordinate:
            return []

        cache_key = f"clearlydefined::{coordinate}"
        data = self.cache.get(cache_key)
        if data is None:
            data = self._fetch_definition(coordinate)
            if data is not None:
                self.cache.set(cache_key, data)

        if not data:
            return []

        license_expression = self._extract_license_expression(data)
        if not license_expression:
            return []

        confidence = self._extract_confidence(data)
        url = self._extract_source_url(data)
        return [
            LicenseEvidence(
                source="clearlydefined",
                license_expression=license_expression,
                confidence=confidence,
                raw_data=data,
                url=url,
            )
        ]

    def _fetch_definition(self, coordinate: str) -> dict | None:
        url = f"{self.BASE_URL}/{coordinate}"
        timeout = float(self.config.timeouts.get("clearlydefined", self.config.timeouts.get("default", 10.0)))
        try:
            response = requests.get(url, timeout=timeout)
        except requests.RequestException:
            return None
        if response.status_code == 404:
            return {}
        if response.status_code >= 400:
            return {}
        try:
            return response.json()
        except ValueError:
            return {}

    def _build_coordinate(self, component: Component) -> str | None:
        if component.version in (None, "", "*"):
            return None
        mapping = self._type_mapping(component)
        if not mapping:
            return None
        type_id, provider = mapping
        namespace = self._normalise_namespace(component, provider)
        version = component.version
        if component.type == ComponentType.GO and provider == "github":
            name = component.name.split("/")[-1]
        else:
            name = component.name
        return f"{type_id}/{provider}/{namespace}/{name}/{version}"

    def _type_mapping(self, component: Component) -> tuple[str, str] | None:
        if component.type == ComponentType.PYTHON:
            return ("pypi", "pypi")
        if component.type == ComponentType.JAVASCRIPT:
            return ("npm", "npmjs")
        if component.type == ComponentType.GO:
            if component.name.startswith("github.com/"):
                return ("golang", "github")
            return ("golang", "-")
        return None

    def _normalise_namespace(self, component: Component, provider: str) -> str:
        if provider == "github" and component.name.startswith("github.com/"):
            parts = component.name.split("/")
            namespace_parts = parts[1:-1] or ["-"]
            return "/".join(namespace_parts)
        if component.namespace:
            return component.namespace
        return "-"

    def _extract_license_expression(self, data: dict) -> str | None:
        licensed = data.get("licensed", {})
        declared = licensed.get("declared")
        if isinstance(declared, str) and declared:
            return declared
        discovered = licensed.get("discovered", {})
        expressions = discovered.get("expressions")
        if isinstance(expressions, list) and expressions:
            return expressions[0]
        return None

    def _extract_confidence(self, data: dict) -> float:
        scores = data.get("scores", {})
        legal_score = scores.get("legal")
        if isinstance(legal_score, (int, float)):
            return max(0.0, min(1.0, float(legal_score) / 100.0))
        return 0.7

    def _extract_source_url(self, data: dict) -> str | None:
        described = data.get("described", {})
        urls = described.get("urls", {})
        if isinstance(urls, dict):
            for key in ("registry", "license", "download"):
                value = urls.get(key)
                if isinstance(value, str):
                    return value
        return None
