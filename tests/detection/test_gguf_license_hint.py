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

"""GGUF license hint must match whole words, not substrings (finding C4)."""

from __future__ import annotations

from pathlib import Path

from lcc.detection.huggingface import HuggingFaceDetector


def _write_gguf(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "model.gguf"
    path.write_bytes(b"GGUF" + b"\x00" * 8 + text.encode("utf-8"))
    return path


def test_mit_not_detected_inside_unrelated_words(tmp_path):
    # "commit" and "limit" both contain "mit"; neither is an MIT license.
    gguf = _write_gguf(tmp_path, "initial commit, memory limit reached, llama 3 weights")
    meta = HuggingFaceDetector()._extract_gguf_metadata(gguf)
    assert meta.get("detected_license_hint") == "llama 3"


def test_mit_detected_as_whole_word(tmp_path):
    gguf = _write_gguf(tmp_path, "license: mit\nsome tensor data")
    meta = HuggingFaceDetector()._extract_gguf_metadata(gguf)
    assert meta.get("detected_license_hint") == "mit"


def test_llama_source_inferred(tmp_path):
    gguf = tmp_path / "Llama-3.1-8B-Q4.gguf"
    gguf.write_bytes(b"GGUF" + b"\x00" * 8 + b"weights")
    meta = HuggingFaceDetector()._extract_gguf_metadata(gguf)
    assert meta.get("inferred_source") == "meta-llama"
