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
Configuration loading utilities.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    yaml = None
from platformdirs import user_cache_dir

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return None  # Fallback if not installed

# Load environment variables from .env file
load_dotenv()

DEFAULT_CONFIG_PATH = Path.home() / ".lcc" / "config.yml"


@dataclass(slots=True)
class LCCConfig:
    """
    High-level configuration model.
    """

    cache_dir: Path = field(
        default_factory=lambda: Path(os.getenv("LCC_CACHE_DIR", user_cache_dir("lcc", "License Compliance Checker")))
    )
    log_level: str = os.getenv("LCC_LOG_LEVEL", "INFO")
    api_tokens: dict[str, str] = field(default_factory=dict)
    timeouts: dict[str, float] = field(default_factory=lambda: {"default": 10.0})
    offline: bool = os.getenv("LCC_OFFLINE", "0") in {"1", "true", "TRUE"}
    active_policy: str | None = None
    policy_context: str | None = os.getenv("LCC_POLICY_CONTEXT")
    opa_url: str | None = os.getenv("LCC_OPA_URL")
    opa_token: str | None = os.getenv("LCC_OPA_TOKEN")
    exclude_patterns: list[str] = field(default_factory=list)
    database_path: Path = field(
        default_factory=lambda: Path(os.getenv("LCC_DB_PATH", Path.home() / ".lcc" / "lcc.db"))
    )
    database_url: str | None = os.getenv("LCC_DATABASE_URL")
    decision_log_path: Path = field(
        default_factory=lambda: Path(os.getenv("LCC_DECISION_LOG", Path.home() / ".lcc" / "decisions.jsonl"))
    )
    redis_url: str | None = os.getenv("LCC_REDIS_URL")
    cache_ttls: dict[str, int] = field(default_factory=dict)
    template_dir: Path = field(
        default_factory=lambda: Path(os.getenv("LCC_TEMPLATE_DIR", Path.home() / ".lcc" / "template-policies"))
    )
    # Treatment for components with UNKNOWN licenses when no policy is applied
    # Options: "violation" (default), "warning", "pass"
    unknown_license_treatment: str = os.getenv("LCC_UNKNOWN_LICENSE_TREATMENT", "violation")

    # LLM Configuration
    # NOTE: LLM-based license analysis is disabled by default (local-only).
    # To enable cloud-based analysis, explicitly set LCC_LLM_PROVIDER and the
    # corresponding API key. Be aware that source code snippets will be sent
    # to the configured provider for license classification.
    llm_endpoint: str | None = os.getenv("LCC_LLM_ENDPOINT")
    llm_model: str = os.getenv("LCC_LLM_MODEL", "accounts/fireworks/models/llama-v3p3-70b-instruct")
    llm_api_key: str = os.getenv("LCC_LLM_API_KEY", "dummy")
    llm_provider: str = os.getenv("LCC_LLM_PROVIDER", "disabled")  # "disabled", "local", or "fireworks"
    fireworks_api_key: str | None = os.getenv("LCC_FIREWORKS_API_KEY")


def load_config(path: Path | None = None) -> LCCConfig:
    """
    Load configuration from disk while honoring environment overrides.
    """

    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.exists():
        return LCCConfig()

    if yaml is None:
        return LCCConfig()

    with config_path.open("r", encoding="utf-8") as handle:
        data: dict[str, Any] = yaml.safe_load(handle) or {}

    cfg = LCCConfig()
    for key, value in data.items():
        if hasattr(cfg, key):
            setattr(cfg, key, value)
    if isinstance(cfg.decision_log_path, str):
        cfg.decision_log_path = Path(cfg.decision_log_path)
    if isinstance(cfg.template_dir, str):
        cfg.template_dir = Path(cfg.template_dir)
    if isinstance(cfg.cache_dir, str):
        cfg.cache_dir = Path(cfg.cache_dir)
    if isinstance(cfg.database_path, str):
        cfg.database_path = Path(cfg.database_path)
    if isinstance(cfg.cache_ttls, dict):
        cfg.cache_ttls = {str(key): int(value) for key, value in cfg.cache_ttls.items()}
    return cfg
