"""Tests for lcc.regulatory.constants — reference data integrity."""

from __future__ import annotations

import pytest

from lcc.regulatory.constants import (
    EU_AI_ACT_ARTICLE_53_OBLIGATIONS,
    ISO_42001_CONTROL_AREAS,
    NIST_AI_RMF_FUNCTIONS,
    RAIL_RESTRICTION_CATEGORIES,
)


# ------------------------------------------------------------------ #
#  EU AI Act Article 53 obligations                                    #
# ------------------------------------------------------------------ #


class TestEUAIActArticle53Obligations:
    def test_count(self):
        assert len(EU_AI_ACT_ARTICLE_53_OBLIGATIONS) == 5

    def test_required_keys(self):
        """Every obligation dict must have article, title, description."""
        for ob in EU_AI_ACT_ARTICLE_53_OBLIGATIONS:
            assert "article" in ob, f"Missing 'article' in {ob}"
            assert "title" in ob, f"Missing 'title' in {ob}"
            assert "description" in ob, f"Missing 'description' in {ob}"

    def test_articles_are_strings(self):
        for ob in EU_AI_ACT_ARTICLE_53_OBLIGATIONS:
            assert isinstance(ob["article"], str)
            assert isinstance(ob["title"], str)
            assert isinstance(ob["description"], str)

    def test_article_references(self):
        """Confirm the specific article references are present."""
        articles = [ob["article"] for ob in EU_AI_ACT_ARTICLE_53_OBLIGATIONS]
        assert "Art.53(1)(a)" in articles
        assert "Art.53(1)(b)" in articles
        assert "Art.53(1)(c)" in articles
        assert "Art.53(1)(d)" in articles
        assert "Art.53(2)" in articles

    def test_descriptions_not_empty(self):
        for ob in EU_AI_ACT_ARTICLE_53_OBLIGATIONS:
            assert len(ob["description"]) > 20, (
                f"Description too short for {ob['article']}"
            )


# ------------------------------------------------------------------ #
#  NIST AI RMF Functions                                               #
# ------------------------------------------------------------------ #


class TestNISTAIRMFFunctions:
    def test_count(self):
        assert len(NIST_AI_RMF_FUNCTIONS) == 4

    def test_required_keys(self):
        for func in NIST_AI_RMF_FUNCTIONS:
            assert "function" in func, f"Missing 'function' key in {func}"
            assert "description" in func, f"Missing 'description' key in {func}"

    def test_function_names(self):
        names = [f["function"] for f in NIST_AI_RMF_FUNCTIONS]
        assert "Govern" in names
        assert "Map" in names
        assert "Measure" in names
        assert "Manage" in names

    def test_descriptions_not_empty(self):
        for func in NIST_AI_RMF_FUNCTIONS:
            assert len(func["description"]) > 20


# ------------------------------------------------------------------ #
#  ISO/IEC 42001 Control Areas                                         #
# ------------------------------------------------------------------ #


class TestISO42001ControlAreas:
    def test_count(self):
        assert len(ISO_42001_CONTROL_AREAS) == 9

    def test_required_keys(self):
        for area in ISO_42001_CONTROL_AREAS:
            assert "control_id" in area, f"Missing 'control_id' in {area}"
            assert "title" in area, f"Missing 'title' in {area}"
            assert "description" in area, f"Missing 'description' in {area}"

    def test_control_ids_are_strings(self):
        for area in ISO_42001_CONTROL_AREAS:
            assert isinstance(area["control_id"], str)
            assert area["control_id"].startswith("A.")

    def test_descriptions_not_empty(self):
        for area in ISO_42001_CONTROL_AREAS:
            assert len(area["description"]) > 20


# ------------------------------------------------------------------ #
#  RAIL Restriction Categories                                         #
# ------------------------------------------------------------------ #


class TestRAILRestrictionCategories:
    def test_count(self):
        assert len(RAIL_RESTRICTION_CATEGORIES) == 11

    def test_required_keys(self):
        for cat in RAIL_RESTRICTION_CATEGORIES:
            assert "id" in cat, f"Missing 'id' in {cat}"
            assert "title" in cat, f"Missing 'title' in {cat}"
            assert "description" in cat, f"Missing 'description' in {cat}"

    def test_ids_are_strings(self):
        for cat in RAIL_RESTRICTION_CATEGORIES:
            assert isinstance(cat["id"], str)
            assert len(cat["id"]) > 0

    def test_known_ids_present(self):
        ids = [c["id"] for c in RAIL_RESTRICTION_CATEGORIES]
        assert "no-harm" in ids
        assert "no-illegal-activity" in ids
        assert "no-discrimination" in ids
        assert "attribution-required" in ids

    def test_descriptions_not_empty(self):
        for cat in RAIL_RESTRICTION_CATEGORIES:
            assert len(cat["description"]) > 20
