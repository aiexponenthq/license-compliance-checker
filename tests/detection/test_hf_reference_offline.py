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

"""Offline mode must not reach the HuggingFace Hub API (finding H1)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import lcc.resolution.hf_hub_resolver as hf_hub_resolver
from lcc.detection.huggingface import HuggingFaceReferenceDetector


def _project_with_reference(tmp_path: Path) -> Path:
    (tmp_path / "app.py").write_text(
        'model = AutoModel.from_pretrained("meta-llama/Llama-3.1-8B")\n',
        encoding="utf-8",
    )
    return tmp_path


def test_offline_does_not_call_hub_api(tmp_path, monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("fetch_model_info must not be called in offline mode")

    monkeypatch.setattr(hf_hub_resolver, "fetch_model_info", _boom)

    detector = HuggingFaceReferenceDetector()
    detector.set_config(SimpleNamespace(offline=True, exclude_patterns=[]))

    components = detector.discover(_project_with_reference(tmp_path))

    # The reference is still detected from source, just without hub metadata.
    assert any("Llama-3.1" in c.name or "llama" in c.name.lower() for c in components)


def test_online_does_call_hub_api(tmp_path, monkeypatch):
    calls = []

    def _fake(model_id, hf_token=None):
        calls.append(model_id)
        return None

    monkeypatch.setattr(hf_hub_resolver, "fetch_model_info", _fake)

    detector = HuggingFaceReferenceDetector()
    detector.set_config(SimpleNamespace(offline=False, exclude_patterns=[]))
    detector.discover(_project_with_reference(tmp_path))

    assert calls == ["meta-llama/Llama-3.1-8B"]
