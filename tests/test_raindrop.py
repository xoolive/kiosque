"""Tests for Raindrop.io API integration."""

from kiosque.api.raindrop import RaindropItem, RaindropTag


def test_raindrop_tag_model():
    """Test RaindropTag Pydantic model."""
    tag = RaindropTag(_id="123", name="technology")
    # _id is stored as a regular attribute
    assert tag.name == "technology"


def test_raindrop_item_model():
    """Test RaindropItem Pydantic model with minimal data."""
    item_data = {
        "_id": 123456,
        "title": "Test Article",
        "link": "https://example.com/article",
        "created": "2024-01-01T00:00:00Z",
        "lastUpdate": "2024-01-01T00:00:00Z",
        "collection": {"_id": 1},
        "type": "link",
        "user": {"_id": 1},
    }
    item = RaindropItem(**item_data)
    assert item.id_ == 123456
    assert item.title == "Test Article"
    assert "example.com" in str(item.link)
    assert item.type == "link"
    assert item.tags == []  # Default empty list
    assert item.important is False  # Default


def test_raindrop_item_with_tags():
    """Test RaindropItem with tags."""
    item_data = {
        "_id": 123456,
        "title": "Test Article",
        "link": "https://example.com/article",
        "created": "2024-01-01T00:00:00Z",
        "lastUpdate": "2024-01-01T00:00:00Z",
        "tags": ["python", "testing"],
        "collection": {"_id": 1},
        "type": "article",
        "user": {"_id": 1},
    }
    item = RaindropItem(**item_data)
    assert item.tags == ["python", "testing"]
    assert item.type == "article"


def test_raindrop_item_cover_empty_string():
    """Test that empty string cover is converted to None."""
    item_data = {
        "_id": 123456,
        "title": "Test Article",
        "link": "https://example.com/article",
        "created": "2024-01-01T00:00:00Z",
        "lastUpdate": "2024-01-01T00:00:00Z",
        "cover": "",  # Empty string should become None
        "collection": {"_id": 1},
        "type": "link",
        "user": {"_id": 1},
    }
    item = RaindropItem(**item_data)
    assert item.cover is None
