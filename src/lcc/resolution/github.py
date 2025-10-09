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
GitHub license API resolver.
"""

from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import urlparse

import requests

from lcc.cache import Cache
from lcc.config import LCCConfig
from lcc.models import Component, LicenseEvidence
from lcc.resolution.base import Resolver


class GitHubResolver(Resolver):
    """
    Fetches license metadata from GitHub's REST API.
    """

    BASE_URL = "https://api.github.com/repos/{owner}/{repo}/license"

    def __init__(self, cache: Cache, config: LCCConfig) -> None:
        super().__init__(name="github")
        self.cache = cache
        self.config = config

    def _build_headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json"}
        token = self.config.api_tokens.get("github")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def resolve(self, component: Component) -> Iterable[LicenseEvidence]:
        if getattr(self.config, "offline", False):
            return []
        repository = self._extract_repository(component)
        if not repository:
            return []
        owner, repo = repository
        cache_key = f"github::{owner}/{repo}"
        data = self.cache.get(cache_key)
        if data is None:
            data = self._fetch_license(owner, repo)
            if data is not None:
                self.cache.set(cache_key, data)

        if not data:
            return []

        license_info = data.get("license") or {}
        spdx = license_info.get("spdx_id") or license_info.get("key")
        if not isinstance(spdx, str) or spdx in ("NOASSERTION", "OTHER"):
            return []

        download_url = data.get("download_url")
        confidence = 0.8
        return [
            LicenseEvidence(
                source="github",
                license_expression=spdx,
                confidence=confidence,
                raw_data=data,
                url=download_url,
            )
        ]

    def _fetch_license(self, owner: str, repo: str) -> dict | None:
        url = self.BASE_URL.format(owner=owner, repo=repo)
        timeout = float(self.config.timeouts.get("github", self.config.timeouts.get("default", 10.0)))
        headers = self._build_headers()
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
        except requests.RequestException:
            return None
        if response.status_code == 404:
            return {}
        if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
            return {}
        if response.status_code >= 400:
            return {}
        try:
            return response.json()
        except ValueError:
            return {}

    def _extract_repository(self, component: Component) -> tuple[str, str] | None:
        candidates = []
        metadata_repo = component.metadata.get("repository")
        if isinstance(metadata_repo, str):
            candidates.append(metadata_repo)
        elif isinstance(metadata_repo, dict):
            repo_url = metadata_repo.get("url")
            if isinstance(repo_url, str):
                candidates.append(repo_url)
        homepage = component.metadata.get("homepage")
        if isinstance(homepage, str):
            candidates.append(homepage)
        for source in component.metadata.get("sources", []):
            if not isinstance(source, dict):
                continue
            for key in ("repository", "url", "homepage", "resolved"):
                value = source.get(key)
                if isinstance(value, str):
                    candidates.append(value)
        for candidate in candidates:
            parsed = self._parse_repo(candidate)
            if parsed:
                return parsed
        return None

    def _parse_repo(self, value: str) -> tuple[str, str] | None:
        value = value.strip()
        if not value:
            return None
        if value.startswith("git@github.com:"):
            value = value.split("git@github.com:", 1)[1]
        if value.startswith("https://github.com/") or value.startswith("http://github.com/"):
            parsed = urlparse(value)
            path = parsed.path
        elif value.startswith("github.com/"):
            path = value[len("github.com") + 1 :]
        else:
            path = value
        path = path.strip("/")
        if not path:
            return None
        if path.endswith(".git"):
            path = path[:-4]
        parts = path.split("/")
        if len(parts) < 2:
            return None
        owner, repo = parts[0], parts[1]
        if not owner or not repo:
            return None
        return owner, repo
