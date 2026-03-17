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

"""Comprehensive tests for enhanced DatasetCardParser.

Tests the extraction of data_sources, collection_method, and privacy_info
from dataset cards, plus backward compatibility.
"""

from __future__ import annotations

import textwrap

import pytest

from lcc.ai.dataset_card_parser import DatasetCardInfo, DatasetCardParser


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def parser():
    return DatasetCardParser()


# ---------------------------------------------------------------------------
# Realistic test dataset card strings
# ---------------------------------------------------------------------------

FULL_HF_DATASET_CARD = textwrap.dedent("""\
    ---
    license: cc-by-4.0
    tags:
      - question-answering
      - nlp
    language:
      - en
    task_categories:
      - question-answering
    size_categories: 100K<n<1M
    pretty_name: TestQA Dataset
    annotations_creators:
      - crowdsourced
    source_datasets:
      - wikipedia
      - common_crawl
    ---

    # TestQA Dataset

    A question-answering dataset built from web sources.

    ## Data Sources

    - [Wikipedia](https://en.wikipedia.org/) - English articles
    - [Common Crawl](https://commoncrawl.org/) - Web text
    - News articles from https://news.example.com/archive

    ## Collection Method

    Data was collected using a combination of web scraping and
    crowdsourced annotation. Web pages were crawled between
    January 2023 and June 2023. Annotators were recruited via
    Amazon Mechanical Turk and paid $15/hour.

    ## Personal and Sensitive Information

    The dataset has been filtered to remove personally identifiable
    information (PII) including names, email addresses, phone numbers,
    and social security numbers. However, some public figure names
    remain as they are part of the factual content.

    ## License

    This dataset is released under the CC-BY-4.0 license.
""")

MINIMAL_HF_DATASET_CARD = textwrap.dedent("""\
    ---
    license: mit
    tags:
      - text-classification
    language: en
    ---

    # Simple Classification Dataset

    A basic text classification dataset.
""")

PLAIN_MARKDOWN_DATASET_CARD = textwrap.dedent("""\
    # Custom NLP Dataset

    **License**: Apache-2.0

    ## Source Data

    The data comes from the following sources:
    - Public government records from https://data.gov/
    - Academic papers from https://arxiv.org/
    - User-contributed content

    ## Collection Process

    Data was manually curated by a team of 10 researchers over 6 months.
    Each sample was verified by at least two annotators.

    ## Privacy

    All personal information has been anonymized. Names have been
    replaced with pseudonyms and dates have been generalized.
""")

DATASET_CARD_NO_ENHANCED_SECTIONS = textwrap.dedent("""\
    ---
    license: bsd-3-clause
    tags:
      - image-classification
    language:
      - en
    task_categories:
      - image-classification
    size_categories: 10K<n<100K
    pretty_name: BasicImages
    ---

    # BasicImages

    A basic image classification dataset with labeled images.
""")

DATASET_CARD_WITH_PII_SECTION = textwrap.dedent("""\
    ---
    license: cc-by-sa-4.0
    ---

    # SensitiveData

    ## Personally Identifiable Information

    This dataset contains de-identified medical records. All patient
    names, dates of birth, and medical record numbers have been removed
    or replaced with synthetic values. The de-identification process
    follows HIPAA Safe Harbor guidelines.
""")

DATASET_CARD_WITH_DESCRIPTION_SOURCES = textwrap.dedent("""\
    ---
    license: apache-2.0
    ---

    # DescDataset

    ## Dataset Description

    This dataset was created by combining data from multiple sources
    including [OpenImages](https://storage.googleapis.com/openimages/)
    and [COCO](https://cocodataset.org/).

    ## Dataset Summary

    Contains 500K annotated images from https://example.com/images
""")

DATASET_CARD_COLLECTION_VARIANTS = textwrap.dedent("""\
    ---
    license: mit
    ---

    # VariantDataset

    License: MIT

    ## Initial Data Collection and Normalization

    Data was initially collected from online forums between 2020 and 2022.
    Text was normalized by lowercasing, removing HTML tags, and applying
    Unicode normalization (NFC).
""")

DATASET_CARD_PRIVACY_VARIANTS = textwrap.dedent("""\
    ---
    license: cc-by-4.0
    ---

    # PrivacyVariant

    ## Sensitive Information

    The dataset may contain references to public figures. No private
    individual's data has been intentionally included. Users should
    exercise caution when using the dataset in production systems.
""")


# ===================================================================
# Data Sources Extraction
# ===================================================================

class TestDataSourcesExtraction:
    """Tests for data_sources extraction from dataset cards."""

    def test_data_sources_from_section(self, parser):
        """'## Data Sources' section yields data_sources list."""
        info = parser.parse_content(FULL_HF_DATASET_CARD)
        assert info is not None
        assert len(info.data_sources) > 0

    def test_data_sources_urls_captured(self, parser):
        """URLs in data sources section are captured."""
        info = parser.parse_content(FULL_HF_DATASET_CARD)
        assert info is not None
        urls = [s for s in info.data_sources if s.startswith("http")]
        assert len(urls) >= 1

    def test_data_sources_markdown_links(self, parser):
        """Markdown link URLs are extracted as data sources."""
        info = parser.parse_content(FULL_HF_DATASET_CARD)
        assert info is not None
        all_sources = " ".join(info.data_sources)
        assert "wikipedia" in all_sources.lower() or "en.wikipedia.org" in all_sources

    def test_data_sources_bullet_items(self, parser):
        """Bullet point items from source section are captured."""
        info = parser.parse_content(FULL_HF_DATASET_CARD)
        assert info is not None
        # Bullet items should be captured as cleaned text
        assert len(info.data_sources) >= 3

    def test_source_data_heading(self, parser):
        """'## Source Data' heading is recognized."""
        info = parser.parse_content(PLAIN_MARKDOWN_DATASET_CARD)
        assert info is not None
        assert len(info.data_sources) > 0
        all_sources = " ".join(info.data_sources)
        assert "data.gov" in all_sources or "arxiv.org" in all_sources

    def test_data_sources_from_description(self, parser):
        """Data sources are found from '## Dataset Description' fallback."""
        info = parser.parse_content(DATASET_CARD_WITH_DESCRIPTION_SOURCES)
        assert info is not None
        assert len(info.data_sources) > 0
        all_sources = " ".join(info.data_sources)
        assert "openimages" in all_sources.lower() or "cocodataset" in all_sources.lower()

    def test_no_data_sources_returns_empty(self, parser):
        """Missing data sources sections return empty list."""
        info = parser.parse_content(DATASET_CARD_NO_ENHANCED_SECTIONS)
        assert info is not None
        assert info.data_sources == []

    def test_data_sources_deduplication(self, parser):
        """Duplicate sources are deduplicated."""
        card = textwrap.dedent("""\
            ---
            license: mit
            ---

            # DupDataset

            ## Data Sources

            - [Example](https://example.com/)
            - Another reference to https://example.com/
        """)
        info = parser.parse_content(card)
        assert info is not None
        url_count = sum(
            1 for s in info.data_sources if "example.com" in s
        )
        # URLs should be deduplicated but bullet text may still appear
        # The key is the same URL should not appear twice
        exact_url_count = sum(
            1 for s in info.data_sources if s == "https://example.com/"
        )
        assert exact_url_count <= 1


# ===================================================================
# Collection Method Extraction
# ===================================================================

class TestCollectionMethodExtraction:
    """Tests for collection_method extraction."""

    def test_collection_method_section(self, parser):
        """'## Collection Method' section extracts methodology."""
        info = parser.parse_content(FULL_HF_DATASET_CARD)
        assert info is not None
        assert info.collection_method is not None
        assert "crowdsourced" in info.collection_method.lower() or \
               "web scraping" in info.collection_method.lower()

    def test_collection_process_heading(self, parser):
        """'## Collection Process' heading is recognized."""
        info = parser.parse_content(PLAIN_MARKDOWN_DATASET_CARD)
        assert info is not None
        assert info.collection_method is not None
        assert "manually curated" in info.collection_method.lower()

    def test_initial_data_collection_heading(self, parser):
        """'## Initial Data Collection and Normalization' heading works."""
        info = parser.parse_content(DATASET_CARD_COLLECTION_VARIANTS)
        assert info is not None
        assert info.collection_method is not None
        assert "online forums" in info.collection_method.lower()

    def test_missing_collection_method(self, parser):
        """Missing collection method section returns None."""
        info = parser.parse_content(DATASET_CARD_NO_ENHANCED_SECTIONS)
        assert info is not None
        assert info.collection_method is None

    def test_collection_method_markdown_stripped(self, parser):
        """Markdown formatting is stripped from collection method text."""
        card = textwrap.dedent("""\
            ---
            license: mit
            ---

            # TestDataset

            ## Collection Method

            Data was collected using **automated** scrapers and
            _manual_ review by [annotators](https://example.com).
        """)
        info = parser.parse_content(card)
        assert info is not None
        assert info.collection_method is not None
        assert "**" not in info.collection_method
        assert "[annotators]" not in info.collection_method


# ===================================================================
# Privacy Info Extraction
# ===================================================================

class TestPrivacyInfoExtraction:
    """Tests for privacy_info extraction."""

    def test_personal_and_sensitive_info(self, parser):
        """'## Personal and Sensitive Information' section extracted."""
        info = parser.parse_content(FULL_HF_DATASET_CARD)
        assert info is not None
        assert info.privacy_info is not None
        assert "pii" in info.privacy_info.lower() or \
               "personally identifiable" in info.privacy_info.lower()

    def test_privacy_heading(self, parser):
        """'## Privacy' heading is recognized."""
        info = parser.parse_content(PLAIN_MARKDOWN_DATASET_CARD)
        assert info is not None
        assert info.privacy_info is not None
        assert "anonymized" in info.privacy_info.lower()

    def test_pii_heading(self, parser):
        """'## Personally Identifiable Information' heading works."""
        info = parser.parse_content(DATASET_CARD_WITH_PII_SECTION)
        assert info is not None
        assert info.privacy_info is not None
        assert "hipaa" in info.privacy_info.lower() or \
               "de-identified" in info.privacy_info.lower()

    def test_sensitive_information_heading(self, parser):
        """'## Sensitive Information' heading works."""
        info = parser.parse_content(DATASET_CARD_PRIVACY_VARIANTS)
        assert info is not None
        assert info.privacy_info is not None
        assert "public figures" in info.privacy_info.lower()

    def test_missing_privacy_info(self, parser):
        """Missing privacy section returns None."""
        info = parser.parse_content(DATASET_CARD_NO_ENHANCED_SECTIONS)
        assert info is not None
        assert info.privacy_info is None


# ===================================================================
# Backward Compatibility
# ===================================================================

class TestDatasetCardBackwardCompat:
    """Tests ensuring enhanced parsing does not break original fields."""

    def test_yaml_only_card_original_fields(self, parser):
        """Basic YAML-only card retains all original fields."""
        info = parser.parse_content(DATASET_CARD_NO_ENHANCED_SECTIONS)
        assert info is not None
        assert info.license == "bsd-3-clause"
        assert "image-classification" in info.tags
        assert "en" in info.languages
        assert "image-classification" in info.task_categories
        assert info.size_categories == "10K<n<100K"
        assert info.dataset_name == "BasicImages"

    def test_new_fields_default_none_or_empty(self, parser):
        """New enhanced fields default to None/empty when missing."""
        info = parser.parse_content(DATASET_CARD_NO_ENHANCED_SECTIONS)
        assert info is not None
        assert info.data_sources == []
        assert info.collection_method is None
        assert info.privacy_info is None

    def test_to_dict_backward_compat(self, parser):
        """to_dict() does not include empty enhanced fields."""
        info = parser.parse_content(DATASET_CARD_NO_ENHANCED_SECTIONS)
        assert info is not None
        d = info.to_dict()
        # Original fields should be present
        assert "license" in d
        assert "tags" in d
        assert "languages" in d
        assert "task_categories" in d
        # Enhanced fields should NOT be in dict when empty
        assert "data_sources" not in d
        assert "collection_method" not in d
        assert "privacy_info" not in d

    def test_to_dict_includes_populated_enhanced_fields(self, parser):
        """to_dict() includes enhanced fields when populated."""
        info = parser.parse_content(FULL_HF_DATASET_CARD)
        assert info is not None
        d = info.to_dict()
        assert "data_sources" in d
        assert "collection_method" in d
        assert "privacy_info" in d

    def test_full_card_original_fields_intact(self, parser):
        """Full card with enhanced sections still has original fields."""
        info = parser.parse_content(FULL_HF_DATASET_CARD)
        assert info is not None
        assert info.license == "cc-by-4.0"
        assert "question-answering" in info.tags
        assert "en" in info.languages
        assert "question-answering" in info.task_categories
        assert info.size_categories == "100K<n<1M"
        assert info.dataset_name == "TestQA Dataset"
        assert "crowdsourced" in info.annotations_creators
        assert "wikipedia" in info.source_datasets

    def test_minimal_card_no_crash(self, parser):
        """Minimal HF card parses without error, enhanced fields empty."""
        info = parser.parse_content(MINIMAL_HF_DATASET_CARD)
        assert info is not None
        assert info.license == "mit"
        assert info.data_sources == []
        assert info.collection_method is None
        assert info.privacy_info is None


# ===================================================================
# File-based tests
# ===================================================================

class TestDatasetFileBasedParsing:
    """Tests for parse_file using tmp_path."""

    def test_parse_file_full_card(self, parser, tmp_path):
        """parse_file works with a full dataset card written to disk."""
        card_path = tmp_path / "README.md"
        card_path.write_text(FULL_HF_DATASET_CARD, encoding="utf-8")
        info = parser.parse_file(card_path)
        assert info is not None
        assert info.license == "cc-by-4.0"
        assert len(info.data_sources) > 0
        assert info.collection_method is not None
        assert info.privacy_info is not None

    def test_parse_file_nonexistent(self, parser, tmp_path):
        """parse_file returns None for a nonexistent file."""
        info = parser.parse_file(tmp_path / "nonexistent.md")
        assert info is None

    def test_parse_file_plain_markdown(self, parser, tmp_path):
        """parse_file works with plain markdown dataset card."""
        card_path = tmp_path / "DATASET_CARD.md"
        card_path.write_text(PLAIN_MARKDOWN_DATASET_CARD, encoding="utf-8")
        info = parser.parse_file(card_path)
        assert info is not None
        assert info.license == "Apache-2.0"
        assert len(info.data_sources) > 0
        assert info.collection_method is not None


# ===================================================================
# DatasetCardInfo unit tests
# ===================================================================

class TestDatasetCardInfo:
    """Direct unit tests for DatasetCardInfo."""

    def test_defaults(self):
        """Default construction has empty/None enhanced fields."""
        info = DatasetCardInfo()
        assert info.license is None
        assert info.tags == []
        assert info.languages == []
        assert info.data_sources == []
        assert info.collection_method is None
        assert info.privacy_info is None

    def test_construction_with_enhanced_fields(self):
        """Construction with enhanced fields populates them."""
        info = DatasetCardInfo(
            license="cc-by-4.0",
            data_sources=["Wikipedia", "CommonCrawl"],
            collection_method="Web scraping",
            privacy_info="PII removed",
        )
        assert info.data_sources == ["Wikipedia", "CommonCrawl"]
        assert info.collection_method == "Web scraping"
        assert info.privacy_info == "PII removed"


# ===================================================================
# Edge cases
# ===================================================================

class TestDatasetEdgeCases:
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
        assert info.data_sources == []

    def test_multiple_licenses_joined(self, parser):
        """Multiple licenses in YAML are joined with OR."""
        card = textwrap.dedent("""\
            ---
            license:
              - cc-by-4.0
              - mit
            ---

            # MultiLicense Dataset
        """)
        info = parser.parse_content(card)
        assert info is not None
        assert "cc-by-4.0" in info.license
        assert "mit" in info.license
        assert "OR" in info.license

    def test_convenience_function(self, tmp_path):
        """parse_dataset_card convenience function works."""
        from lcc.ai.dataset_card_parser import parse_dataset_card

        card_path = tmp_path / "README.md"
        card_path.write_text(FULL_HF_DATASET_CARD, encoding="utf-8")
        info = parse_dataset_card(card_path)
        assert info is not None
        assert info.license == "cc-by-4.0"

    def test_level3_heading_recognized(self, parser):
        """### level headings are matched for section extraction."""
        card = textwrap.dedent("""\
            ---
            license: mit
            ---

            # Dataset

            ### Data Sources

            - Source A from https://example.com/a
            - Source B

            ### Personal and Sensitive Information

            No PII is included in this dataset.
        """)
        info = parser.parse_content(card)
        assert info is not None
        assert len(info.data_sources) > 0
        assert info.privacy_info is not None
        assert "pii" in info.privacy_info.lower() or "no pii" in info.privacy_info.lower()
