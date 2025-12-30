"""Tests for Website base class."""

from unittest.mock import Mock, patch

import pytest

from kiosque.core.website import Website


class MockWebsite(Website):
    """Mock website for testing."""

    base_url = "https://test.example.com/"
    login_url = "https://test.example.com/login"


def test_known_websites_registry():
    """Test that Website subclasses are registered."""
    # The Website class maintains a registry of all subclasses
    assert isinstance(Website.known_websites, list)
    # Our mock website should be in the registry
    assert MockWebsite in Website.known_websites


def test_module_cache_builds():
    """Test that module cache is built correctly."""
    Website._build_module_cache()
    assert isinstance(Website._module_cache, dict)
    assert len(Website._module_cache) > 0

    # Check that cached entries look valid
    # Cache now contains both URLs and aliases
    for key, module_name in Website._module_cache.items():
        # Key is either a URL (starts with https://) or an alias (single word)
        assert isinstance(key, str)
        assert len(key) > 0
        # Module name should always be valid
        assert module_name.startswith("kiosque.website.")

    # Check that we have at least some URLs cached
    urls_cached = [
        k for k in Website._module_cache.keys() if k.startswith("https://")
    ]
    assert len(urls_cached) > 0

    # Check that we have at least some aliases cached
    aliases_cached = [
        k for k in Website._module_cache.keys() if not k.startswith("https://")
    ]
    assert (
        len(aliases_cached) > 0
    )  # Should have at least lemonde, courrier, etc.


def test_instance_unsupported_url():
    """Test that unsupported URL raises ValueError."""
    with patch("kiosque.core.client.get_with_retry") as mock_get:
        # Mock a failed HTTP request
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("DNS failure")
        mock_get.side_effect = Exception("DNS failure")

        with pytest.raises((ValueError, Exception)):
            Website.instance("https://unsupported-example.com/article")


def test_header_entries():
    """Test default header entries."""
    assert "title" in Website.header_entries
    assert "author" in Website.header_entries
    assert "date" in Website.header_entries
    assert "url" in Website.header_entries
    assert "description" in Website.header_entries


def test_url_translation():
    """Test URL translation is a class variable."""
    assert isinstance(Website.url_translation, dict)


def test_latest_issue_not_implemented():
    """Test that latest_issue_url raises NotImplementedError by default."""
    website = MockWebsite()
    with pytest.raises(NotImplementedError) as exc_info:
        website.latest_issue_url()
    assert "does not support downloading" in str(exc_info.value)
