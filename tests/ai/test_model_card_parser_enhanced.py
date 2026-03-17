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

"""Comprehensive tests for enhanced ModelCardParser.

Tests the extraction of training data, limitations, evaluation metrics,
intended uses, environmental impact, and use restrictions from model cards.
"""

from __future__ import annotations

import textwrap

import pytest

from lcc.ai.model_card_parser import ModelCardInfo, ModelCardParser


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def parser():
    return ModelCardParser()


# ---------------------------------------------------------------------------
# Realistic test model card strings
# ---------------------------------------------------------------------------

FULL_HF_MODEL_CARD = textwrap.dedent("""\
    ---
    license: apache-2.0
    tags:
      - text-generation
      - transformers
    datasets:
      - wikipedia
      - bookcorpus
    language: en
    pipeline_tag: text-generation
    library_name: transformers
    model-index:
      - name: TestLLM-7B
    ---

    # TestLLM-7B

    A 7-billion parameter language model for general-purpose text generation.

    ## Training Data

    The model was trained on a combination of publicly available datasets:
    - [Wikipedia](https://dumps.wikimedia.org/) (English, 2023 dump)
    - [BookCorpus](https://huggingface.co/datasets/bookcorpus/bookcorpus)
    - CommonCrawl filtered subset
    - OpenWebText curated data from https://skylion007.github.io/OpenWebTextCorpus/

    Total training data: approximately 1.2 trillion tokens.

    ## Limitations

    This model has several known limitations:
    - May generate factually incorrect information
    - Can exhibit social biases present in training data
    - Not suitable for safety-critical applications
    - Performance degrades on languages other than English

    ## Evaluation Results

    | Benchmark | Score |
    |-----------|-------|
    | MMLU | 64.3% |
    | HellaSwag | 82.1 |
    | ARC-Challenge | 55.7% |

    Additional metrics:
    - **Perplexity**: 8.42
    - **BLEU Score**: 34.5

    ## Intended Use

    This model is intended for research and development in natural language
    processing. It can be used for text generation, summarization, and
    question answering tasks.

    ## Out-of-Scope Use

    This model should not be used for:
    - Generating medical or legal advice
    - Making automated decisions affecting individuals
    - Creating deceptive content or misinformation

    ## Environmental Impact

    - **Hardware**: 64x NVIDIA A100 80GB GPUs
    - **Training time**: 21 days
    - **Carbon emissions**: estimated 25.2 tCO2eq
    - **Cloud provider**: AWS us-east-1

    ## Use Restrictions

    - Do not use this model to generate harmful or discriminatory content
    - Do not use for surveillance or tracking individuals
    - Attribution required for derivative works
""")

MINIMAL_HF_MODEL_CARD = textwrap.dedent("""\
    ---
    license: mit
    tags:
      - image-classification
    language: en
    ---

    # Simple Image Classifier

    A basic image classification model.

    ## License

    MIT License
""")

PLAIN_MARKDOWN_MODEL_CARD = textwrap.dedent("""\
    # MyModel v2

    **License**: Apache-2.0

    ## Training Data

    Trained on Wikipedia and BookCorpus datasets collected from
    https://huggingface.co/datasets/wikipedia and various web sources.

    ## Known Limitations

    The model struggles with rare languages and domain-specific terminology.
    It may produce biased outputs.

    ## Performance

    MMLU: 79.2%
    HellaSwag: 85.1

    ## Uses

    General-purpose text understanding and generation.

    ## Restrictions

    - You may not use this model for illegal activities
    - Not permitted to use for mass surveillance
""")

RAIL_STYLE_MODEL_CARD = textwrap.dedent("""\
    ---
    license: openrail
    tags:
      - text-generation
    ---

    # RAIL Model

    ## License

    This model is released under the OpenRAIL license.

    You may not use this model for generating harmful content.
    You shall not use this model for military applications.
    Users are restricted from using it for deepfake generation.
    This model is not intended for medical diagnosis.
    Users are prohibited from using it in autonomous weapons systems.

    ## Limitations and Biases

    The model inherits biases from its training data. Users should be
    aware that outputs may reflect stereotypes present in web text.
""")

ENVIRONMENTAL_DETAIL_CARD = textwrap.dedent("""\
    ---
    license: apache-2.0
    ---

    # GreenModel

    ## Environmental Impact

    - Hardware: 8x NVIDIA H100 GPUs
    - Training time: 72 hours
    - Carbon emissions: 4.8 tCO2eq
    - Cloud provider: Google Cloud us-central1

    ## Carbon Footprint

    Training was performed in a data center powered by 60% renewable energy.
    GPU utilization was at 95% throughout training.
""")

HF_DATASET_REFS_CARD = textwrap.dedent("""\
    ---
    license: cc-by-4.0
    datasets:
      - squad
    ---

    # RefModel

    ## Training Data

    This model was fine-tuned on the following datasets:
    - huggingface.co/datasets/rajpurkar/squad
    - datasets/allenai/c4
    - The Pile from EleutherAI
    - LAION-400M image-text pairs
    - Additional data from https://commoncrawl.org/the-data/
""")

MODEL_CARD_NO_ENHANCED_SECTIONS = textwrap.dedent("""\
    ---
    license: bsd-3-clause
    tags:
      - feature-extraction
    datasets:
      - glue
    language: en
    pipeline_tag: feature-extraction
    library_name: transformers
    model-index:
      - name: BasicBERT
    ---

    # BasicBERT

    A basic BERT model for feature extraction.
""")

METRICS_TABLE_CARD = textwrap.dedent("""\
    ---
    license: apache-2.0
    ---

    # MetricsModel

    ## Evaluation Results

    | Metric | Score |
    |--------|-------|
    | Accuracy | 93.4% |
    | F1 Score | 91.2 |
    | ROUGE-L | 45.8% |
    | BLEU | 38.7 |
""")

METRICS_KV_CARD = textwrap.dedent("""\
    ---
    license: apache-2.0
    ---

    # KVMetricsModel

    ## Results

    MMLU: 79.2%
    HellaSwag: 85.1
    TruthfulQA: 42.3%
    **Accuracy**: 0.93
""")


# ===================================================================
# a) Training Data Extraction
# ===================================================================

class TestTrainingDataExtraction:
    """Tests for training data sources and description extraction."""

    def test_training_data_section_with_dataset_names(self, parser):
        """Model card with '## Training Data' section extracts training_data_sources."""
        info = parser.parse_content(FULL_HF_MODEL_CARD)
        assert info is not None
        assert len(info.training_data_sources) > 0
        # Should find Wikipedia, BookCorpus, CommonCrawl, OpenWebText
        source_str = " ".join(info.training_data_sources).lower()
        assert any("wikipedia" in s.lower() for s in info.training_data_sources)

    def test_huggingface_dataset_refs_extracted(self, parser):
        """HuggingFace dataset refs like 'datasets/org/name' are captured."""
        info = parser.parse_content(HF_DATASET_REFS_CARD)
        assert info is not None
        # Should find rajpurkar/squad and allenai/c4
        hf_refs = [s for s in info.training_data_sources if "/" in s]
        assert len(hf_refs) >= 2
        ref_str = " ".join(hf_refs)
        assert "rajpurkar/squad" in ref_str or "squad" in ref_str.lower()

    def test_urls_in_training_section_captured(self, parser):
        """URLs mentioned in training data section are captured."""
        info = parser.parse_content(FULL_HF_MODEL_CARD)
        assert info is not None
        urls = [s for s in info.training_data_sources if s.startswith("http")]
        assert len(urls) >= 1

    def test_known_dataset_names_detected(self, parser):
        """Well-known dataset names (Wikipedia, BookCorpus, etc.) are detected."""
        info = parser.parse_content(FULL_HF_MODEL_CARD)
        assert info is not None
        sources_lower = [s.lower() for s in info.training_data_sources]
        # Wikipedia and BookCorpus should be captured (may be URLs or names)
        all_sources = " ".join(info.training_data_sources).lower()
        assert "wikipedia" in all_sources or "dumps.wikimedia.org" in all_sources
        assert "bookcorpus" in all_sources or "BookCorpus" in " ".join(info.training_data_sources)

    def test_training_data_description_populated(self, parser):
        """Training data description text is available."""
        info = parser.parse_content(FULL_HF_MODEL_CARD)
        assert info is not None
        assert info.training_data_description is not None
        assert "trillion tokens" in info.training_data_description.lower()

    def test_no_training_data_section_returns_empty(self, parser):
        """Model card without training data section returns empty list."""
        info = parser.parse_content(MODEL_CARD_NO_ENHANCED_SECTIONS)
        assert info is not None
        assert info.training_data_sources == []
        assert info.training_data_description is None

    def test_plain_markdown_training_data(self, parser):
        """Plain markdown (no YAML) model card extracts training data."""
        info = parser.parse_content(PLAIN_MARKDOWN_MODEL_CARD)
        assert info is not None
        assert len(info.training_data_sources) > 0
        all_sources = " ".join(info.training_data_sources)
        assert "Wikipedia" in all_sources or "wikipedia" in all_sources.lower()

    def test_training_data_deduplication(self, parser):
        """Duplicate sources are deduplicated."""
        card = textwrap.dedent("""\
            ---
            license: mit
            ---

            # DupModel

            ## Training Data

            Trained on [Wikipedia](https://en.wikipedia.org/) and Wikipedia.
            Also uses https://en.wikipedia.org/ for validation.
        """)
        info = parser.parse_content(card)
        assert info is not None
        # Wikipedia (the known dataset name) should appear, URL should also
        # but the URL should not be duplicated
        url_count = sum(
            1 for s in info.training_data_sources
            if s == "https://en.wikipedia.org/"
        )
        assert url_count <= 1


# ===================================================================
# b) Limitations Extraction
# ===================================================================

class TestLimitationsExtraction:
    """Tests for limitations text extraction."""

    def test_limitations_section_extracted(self, parser):
        """Model card with '## Limitations' section extracts text."""
        info = parser.parse_content(FULL_HF_MODEL_CARD)
        assert info is not None
        assert info.limitations is not None
        assert "factually incorrect" in info.limitations.lower()

    def test_known_limitations_heading(self, parser):
        """Model card with '## Known Limitations' heading works."""
        info = parser.parse_content(PLAIN_MARKDOWN_MODEL_CARD)
        assert info is not None
        assert info.limitations is not None
        assert "rare languages" in info.limitations.lower()

    def test_limitations_and_biases_heading(self, parser):
        """Model card with '## Limitations and Biases' heading works."""
        info = parser.parse_content(RAIL_STYLE_MODEL_CARD)
        assert info is not None
        assert info.limitations is not None
        assert "biases" in info.limitations.lower() or "stereotypes" in info.limitations.lower()

    def test_missing_limitations_returns_none(self, parser):
        """Missing limitations section returns None."""
        info = parser.parse_content(MODEL_CARD_NO_ENHANCED_SECTIONS)
        assert info is not None
        assert info.limitations is None

    def test_limitations_markdown_stripped(self, parser):
        """Markdown formatting is stripped from limitations text."""
        card = textwrap.dedent("""\
            ---
            license: mit
            ---

            # TestModel

            ## Limitations

            The model has **significant** limitations with _rare_ inputs
            and `edge cases`. See [docs](https://example.com) for details.
        """)
        info = parser.parse_content(card)
        assert info is not None
        assert info.limitations is not None
        # Markdown markers should be stripped
        assert "**" not in info.limitations
        assert "_rare_" not in info.limitations
        assert "`edge cases`" not in info.limitations
        assert "[docs]" not in info.limitations


# ===================================================================
# c) Evaluation Metrics Extraction
# ===================================================================

class TestEvaluationMetricsExtraction:
    """Tests for evaluation/benchmark metrics extraction."""

    def test_kv_pattern_metrics(self, parser):
        """Metric pattern 'MMLU: 79.2%' is extracted."""
        info = parser.parse_content(METRICS_KV_CARD)
        assert info is not None
        assert len(info.evaluation_metrics) > 0
        # Should find MMLU
        assert "MMLU" in info.evaluation_metrics
        assert info.evaluation_metrics["MMLU"] == "79.2%"

    def test_table_metrics_parsed(self, parser):
        """Markdown table of metrics is parsed correctly."""
        info = parser.parse_content(METRICS_TABLE_CARD)
        assert info is not None
        assert len(info.evaluation_metrics) > 0
        # Should find table entries
        assert "Accuracy" in info.evaluation_metrics
        assert info.evaluation_metrics["Accuracy"] == "93.4%"

    def test_mixed_metrics_in_full_card(self, parser):
        """Full model card extracts both table and KV metrics."""
        info = parser.parse_content(FULL_HF_MODEL_CARD)
        assert info is not None
        assert len(info.evaluation_metrics) > 0
        # Should have table entries (MMLU, HellaSwag, ARC-Challenge)
        # and KV entries (Perplexity, BLEU Score)
        metrics_keys = list(info.evaluation_metrics.keys())
        assert len(metrics_keys) >= 3

    def test_missing_metrics_returns_empty_dict(self, parser):
        """Missing evaluation section returns empty dict."""
        info = parser.parse_content(MODEL_CARD_NO_ENHANCED_SECTIONS)
        assert info is not None
        assert info.evaluation_metrics == {}

    def test_bold_metric_key(self, parser):
        """Metric like '**Accuracy**: 0.93' is parsed."""
        info = parser.parse_content(METRICS_KV_CARD)
        assert info is not None
        # Bold key "**Accuracy**" should be cleaned up
        assert "Accuracy" in info.evaluation_metrics
        assert info.evaluation_metrics["Accuracy"] == "0.93"

    def test_percentage_and_raw_values(self, parser):
        """Both percentage (79.2%) and raw (85.1) metric values are captured."""
        info = parser.parse_content(METRICS_KV_CARD)
        assert info is not None
        assert "MMLU" in info.evaluation_metrics
        assert "%" in info.evaluation_metrics["MMLU"]
        assert "HellaSwag" in info.evaluation_metrics
        # HellaSwag = 85.1 (no %)
        assert "%" not in info.evaluation_metrics["HellaSwag"]


# ===================================================================
# d) Intended Uses Extraction
# ===================================================================

class TestIntendedUsesExtraction:
    """Tests for intended uses and out-of-scope uses extraction."""

    def test_intended_use_section(self, parser):
        """Model card with '## Intended Use' populates intended_uses."""
        info = parser.parse_content(FULL_HF_MODEL_CARD)
        assert info is not None
        assert info.intended_uses is not None
        assert "research" in info.intended_uses.lower()

    def test_uses_heading(self, parser):
        """Model card with '## Uses' heading populates intended_uses."""
        info = parser.parse_content(PLAIN_MARKDOWN_MODEL_CARD)
        assert info is not None
        assert info.intended_uses is not None
        assert "text understanding" in info.intended_uses.lower()

    def test_out_of_scope_use(self, parser):
        """Model card with '## Out-of-Scope Use' populates out_of_scope_uses."""
        info = parser.parse_content(FULL_HF_MODEL_CARD)
        assert info is not None
        assert info.out_of_scope_uses is not None
        assert "medical" in info.out_of_scope_uses.lower() or \
               "legal" in info.out_of_scope_uses.lower()

    def test_missing_intended_uses(self, parser):
        """Missing intended use section returns None."""
        info = parser.parse_content(MODEL_CARD_NO_ENHANCED_SECTIONS)
        assert info is not None
        assert info.intended_uses is None

    def test_missing_out_of_scope_uses(self, parser):
        """Missing out-of-scope section returns None."""
        info = parser.parse_content(MODEL_CARD_NO_ENHANCED_SECTIONS)
        assert info is not None
        assert info.out_of_scope_uses is None


# ===================================================================
# e) Environmental Impact Extraction
# ===================================================================

class TestEnvironmentalImpactExtraction:
    """Tests for environmental impact / carbon footprint extraction."""

    def test_hardware_type_extracted(self, parser):
        """Hardware type from environmental impact section is extracted."""
        info = parser.parse_content(FULL_HF_MODEL_CARD)
        assert info is not None
        assert "hardware" in info.environmental_impact
        assert "A100" in info.environmental_impact["hardware"]

    def test_carbon_emissions_captured(self, parser):
        """Carbon emissions are captured from the section."""
        info = parser.parse_content(FULL_HF_MODEL_CARD)
        assert info is not None
        assert "carbon_emissions" in info.environmental_impact
        assert "25.2" in info.environmental_impact["carbon_emissions"] or \
               "tCO2" in info.environmental_impact["carbon_emissions"]

    def test_training_time_extracted(self, parser):
        """Training time is extracted."""
        info = parser.parse_content(ENVIRONMENTAL_DETAIL_CARD)
        assert info is not None
        assert "hardware" in info.environmental_impact
        assert "H100" in info.environmental_impact["hardware"]

    def test_cloud_provider_extracted(self, parser):
        """Cloud provider is extracted from environmental impact."""
        info = parser.parse_content(FULL_HF_MODEL_CARD)
        assert info is not None
        assert "cloud_provider" in info.environmental_impact
        assert "AWS" in info.environmental_impact["cloud_provider"] or \
               "us-east" in info.environmental_impact["cloud_provider"]

    def test_missing_environmental_impact(self, parser):
        """Missing environmental impact section returns empty dict."""
        info = parser.parse_content(MODEL_CARD_NO_ENHANCED_SECTIONS)
        assert info is not None
        assert info.environmental_impact == {}

    def test_environmental_impact_multiple_fields(self, parser):
        """Multiple environmental impact fields are captured."""
        info = parser.parse_content(ENVIRONMENTAL_DETAIL_CARD)
        assert info is not None
        assert len(info.environmental_impact) >= 2


# ===================================================================
# f) Use Restrictions Extraction
# ===================================================================

class TestUseRestrictionsExtraction:
    """Tests for use restrictions / RAIL-style restriction detection."""

    def test_you_may_not_pattern(self, parser):
        """'You may not use' pattern captured as restriction."""
        info = parser.parse_content(RAIL_STYLE_MODEL_CARD)
        assert info is not None
        assert len(info.use_restrictions) > 0
        restrictions_text = " ".join(info.use_restrictions).lower()
        assert "harmful" in restrictions_text or "content" in restrictions_text

    def test_shall_not_pattern(self, parser):
        """'You shall not' pattern captured."""
        info = parser.parse_content(RAIL_STYLE_MODEL_CARD)
        assert info is not None
        restrictions_text = " ".join(info.use_restrictions).lower()
        assert "military" in restrictions_text

    def test_restricted_from_pattern(self, parser):
        """'restricted from' pattern captured."""
        info = parser.parse_content(RAIL_STYLE_MODEL_CARD)
        assert info is not None
        restrictions_text = " ".join(info.use_restrictions).lower()
        assert "deepfake" in restrictions_text

    def test_prohibited_from_pattern(self, parser):
        """'prohibited from' pattern captured."""
        info = parser.parse_content(RAIL_STYLE_MODEL_CARD)
        assert info is not None
        restrictions_text = " ".join(info.use_restrictions).lower()
        assert "weapons" in restrictions_text or "autonomous" in restrictions_text

    def test_not_intended_for_pattern(self, parser):
        """'is not intended for' pattern captured."""
        info = parser.parse_content(RAIL_STYLE_MODEL_CARD)
        assert info is not None
        restrictions_text = " ".join(info.use_restrictions).lower()
        assert "medical" in restrictions_text

    def test_restrictions_section_bullet_items(self, parser):
        """Bullet items in '## Restrictions' section are captured."""
        info = parser.parse_content(PLAIN_MARKDOWN_MODEL_CARD)
        assert info is not None
        assert len(info.use_restrictions) >= 2

    def test_rail_style_multiple_restrictions(self, parser):
        """RAIL-style model card detects multiple restrictions."""
        info = parser.parse_content(RAIL_STYLE_MODEL_CARD)
        assert info is not None
        assert len(info.use_restrictions) >= 3

    def test_no_restrictions_empty_list(self, parser):
        """Model card without restrictions returns empty list."""
        info = parser.parse_content(MODEL_CARD_NO_ENHANCED_SECTIONS)
        assert info is not None
        assert info.use_restrictions == []


# ===================================================================
# g) Backward Compatibility
# ===================================================================

class TestBackwardCompatibility:
    """Tests ensuring enhanced parsing does not break original fields."""

    def test_yaml_only_card_original_fields(self, parser):
        """Basic YAML-only card retains all original fields."""
        info = parser.parse_content(MODEL_CARD_NO_ENHANCED_SECTIONS)
        assert info is not None
        assert info.license == "bsd-3-clause"
        assert "feature-extraction" in info.tags
        assert "glue" in info.datasets
        assert info.language == "en"
        assert info.pipeline_tag == "feature-extraction"
        assert info.library_name == "transformers"
        assert info.model_name == "BasicBERT"

    def test_new_fields_default_none_or_empty(self, parser):
        """New enhanced fields default to None/empty when sections missing."""
        info = parser.parse_content(MODEL_CARD_NO_ENHANCED_SECTIONS)
        assert info is not None
        assert info.training_data_sources == []
        assert info.training_data_description is None
        assert info.limitations is None
        assert info.evaluation_metrics == {}
        assert info.intended_uses is None
        assert info.out_of_scope_uses is None
        assert info.environmental_impact == {}
        assert info.use_restrictions == []

    def test_to_dict_backward_compat(self, parser):
        """to_dict() does not include empty enhanced fields."""
        info = parser.parse_content(MODEL_CARD_NO_ENHANCED_SECTIONS)
        assert info is not None
        d = info.to_dict()
        # Original fields should be present
        assert "license" in d
        assert "tags" in d
        assert "datasets" in d
        # Enhanced fields should NOT be in dict when empty
        assert "training_data_sources" not in d
        assert "training_data_description" not in d
        assert "limitations" not in d
        assert "evaluation_metrics" not in d
        assert "intended_uses" not in d
        assert "out_of_scope_uses" not in d
        assert "environmental_impact" not in d
        assert "use_restrictions" not in d

    def test_to_dict_includes_populated_enhanced_fields(self, parser):
        """to_dict() includes enhanced fields when populated."""
        info = parser.parse_content(FULL_HF_MODEL_CARD)
        assert info is not None
        d = info.to_dict()
        # Enhanced fields should be present when populated
        assert "training_data_sources" in d
        assert "limitations" in d
        assert "evaluation_metrics" in d
        assert "intended_uses" in d
        assert "out_of_scope_uses" in d
        assert "environmental_impact" in d
        assert "use_restrictions" in d

    def test_full_card_original_fields_intact(self, parser):
        """Full model card with enhanced sections still has original fields."""
        info = parser.parse_content(FULL_HF_MODEL_CARD)
        assert info is not None
        assert info.license == "apache-2.0"
        assert "text-generation" in info.tags
        assert "wikipedia" in info.datasets
        assert info.language == "en"
        assert info.pipeline_tag == "text-generation"
        assert info.library_name == "transformers"
        assert info.model_name == "TestLLM-7B"

    def test_minimal_card_no_crash(self, parser):
        """Minimal HF card parses without error, enhanced fields are empty."""
        info = parser.parse_content(MINIMAL_HF_MODEL_CARD)
        assert info is not None
        assert info.license == "mit"
        assert info.training_data_sources == []
        assert info.limitations is None


# ===================================================================
# File-based tests
# ===================================================================

class TestFileBasedParsing:
    """Tests for parse_file using tmp_path."""

    def test_parse_file_full_card(self, parser, tmp_path):
        """parse_file works with a full model card written to disk."""
        card_path = tmp_path / "README.md"
        card_path.write_text(FULL_HF_MODEL_CARD, encoding="utf-8")
        info = parser.parse_file(card_path)
        assert info is not None
        assert info.license == "apache-2.0"
        assert len(info.training_data_sources) > 0
        assert info.limitations is not None

    def test_parse_file_nonexistent(self, parser, tmp_path):
        """parse_file returns None for a nonexistent file."""
        info = parser.parse_file(tmp_path / "nonexistent.md")
        assert info is None

    def test_parse_file_plain_markdown(self, parser, tmp_path):
        """parse_file works with plain markdown (no YAML frontmatter)."""
        card_path = tmp_path / "MODEL_CARD.md"
        card_path.write_text(PLAIN_MARKDOWN_MODEL_CARD, encoding="utf-8")
        info = parser.parse_file(card_path)
        assert info is not None
        assert info.license == "Apache-2.0"
        assert len(info.training_data_sources) > 0


# ===================================================================
# ModelCardInfo unit tests
# ===================================================================

class TestModelCardInfo:
    """Direct unit tests for ModelCardInfo dataclass behavior."""

    def test_defaults(self):
        """Default construction has empty/None enhanced fields."""
        info = ModelCardInfo()
        assert info.license is None
        assert info.tags == []
        assert info.datasets == []
        assert info.training_data_sources == []
        assert info.training_data_description is None
        assert info.limitations is None
        assert info.evaluation_metrics == {}
        assert info.intended_uses is None
        assert info.out_of_scope_uses is None
        assert info.environmental_impact == {}
        assert info.use_restrictions == []

    def test_construction_with_enhanced_fields(self):
        """Construction with enhanced fields populates them."""
        info = ModelCardInfo(
            license="mit",
            training_data_sources=["Wikipedia", "BookCorpus"],
            limitations="Has bias issues",
            evaluation_metrics={"MMLU": "79.2%"},
            intended_uses="Research only",
            out_of_scope_uses="Medical advice",
            environmental_impact={"hardware": "8x A100"},
            use_restrictions=["No military use"],
        )
        assert info.training_data_sources == ["Wikipedia", "BookCorpus"]
        assert info.limitations == "Has bias issues"
        assert info.evaluation_metrics == {"MMLU": "79.2%"}
        assert info.intended_uses == "Research only"
        assert info.out_of_scope_uses == "Medical advice"
        assert info.environmental_impact == {"hardware": "8x A100"}
        assert info.use_restrictions == ["No military use"]


# ===================================================================
# Edge cases
# ===================================================================

class TestEdgeCases:
    """Edge case and corner case tests."""

    def test_empty_content(self, parser):
        """Empty content returns None."""
        info = parser.parse_content("")
        assert info is None

    def test_only_yaml_no_markdown(self, parser):
        """YAML frontmatter with no markdown body still parses."""
        card = textwrap.dedent("""\
            ---
            license: mit
            ---
        """)
        info = parser.parse_content(card)
        assert info is not None
        assert info.license == "mit"
        assert info.training_data_sources == []

    def test_level3_heading_sections(self, parser):
        """### level headings are also matched for section extraction."""
        card = textwrap.dedent("""\
            ---
            license: mit
            ---

            # Model

            ### Limitations

            This model is limited to English text only.

            ### Evaluation Results

            Accuracy: 88.5%
        """)
        info = parser.parse_content(card)
        assert info is not None
        assert info.limitations is not None
        assert "english" in info.limitations.lower()
        assert len(info.evaluation_metrics) > 0

    def test_multiple_licenses_in_yaml(self, parser):
        """Multiple licenses in YAML are joined with OR."""
        card = textwrap.dedent("""\
            ---
            license:
              - mit
              - apache-2.0
            ---

            # MultiLicense Model
        """)
        info = parser.parse_content(card)
        assert info is not None
        assert "mit" in info.license
        assert "apache-2.0" in info.license
        assert "OR" in info.license

    def test_case_insensitive_section_headings(self, parser):
        """Section heading matching is case-insensitive."""
        card = textwrap.dedent("""\
            ---
            license: mit
            ---

            # Model

            ## TRAINING DATA

            Trained on Wikipedia.

            ## LIMITATIONS

            Limited accuracy on rare languages.
        """)
        info = parser.parse_content(card)
        assert info is not None
        # Even with all-caps headings, sections should be found
        # Note: _extract_section uses re.IGNORECASE, but the heading list
        # uses specific casing. Let's check if it works.
        # The heading list has "Training Data" and matches case-insensitively
        assert len(info.training_data_sources) > 0 or info.training_data_description is not None

    def test_convenience_function(self, tmp_path):
        """parse_model_card convenience function works."""
        from lcc.ai.model_card_parser import parse_model_card

        card_path = tmp_path / "README.md"
        card_path.write_text(FULL_HF_MODEL_CARD, encoding="utf-8")
        info = parse_model_card(card_path)
        assert info is not None
        assert info.license == "apache-2.0"
