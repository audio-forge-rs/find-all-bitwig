"""Tests for search functionality."""

import pytest

from bwctl.db.models import ContentType, SearchResult


def test_search_result_from_row():
    """Test creating SearchResult from database row."""
    row = {
        "id": 1,
        "name": "Test Preset",
        "content_type": "preset",
        "category": "Bass",
        "parent_device": "Polymer",
        "file_path": "/path/to/preset.bwpreset",
        "package_name": "Essentials",
        "relevance": 0.95,
    }

    result = SearchResult.from_row(row)

    assert result.id == 1
    assert result.name == "Test Preset"
    assert result.content_type == ContentType.PRESET
    assert result.category == "Bass"
    assert result.parent_device == "Polymer"
    assert result.relevance == 0.95


def test_content_type_enum():
    """Test ContentType enum values."""
    assert ContentType.PRESET.value == "preset"
    assert ContentType.SAMPLE.value == "sample"
    assert ContentType("preset") == ContentType.PRESET
