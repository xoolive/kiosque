"""Tests for configuration module."""

import pytest
from pydantic import ValidationError

from kiosque.core.config import (
    RaindropConfig,
    WebsiteCredentials,
)


def test_website_credentials_valid():
    """Test valid website credentials."""
    creds = WebsiteCredentials(username="test@example.com", password="secret")
    assert creds.username == "test@example.com"
    assert creds.password == "secret"
    assert creds.alias is None


def test_website_credentials_with_alias():
    """Test website credentials with alias."""
    creds = WebsiteCredentials(
        username="test@example.com", password="secret", alias="news,paper"
    )
    assert creds.alias == "news,paper"


def test_website_credentials_empty_username():
    """Test that empty username raises validation error."""
    with pytest.raises(ValidationError):
        WebsiteCredentials(username="", password="secret")


def test_website_credentials_empty_password():
    """Test that empty password raises validation error."""
    with pytest.raises(ValidationError):
        WebsiteCredentials(username="test@example.com", password="")


def test_raindrop_config_valid():
    """Test valid Raindrop.io configuration."""
    config = RaindropConfig(token="test_token_123")
    assert config.token == "test_token_123"


def test_raindrop_config_empty_token():
    """Test that empty token raises validation error."""
    with pytest.raises(ValidationError):
        RaindropConfig(token="")


def test_raindrop_config_strips_whitespace():
    """Test that token whitespace is stripped."""
    config = RaindropConfig(token="  test_token_123  ")
    assert config.token == "test_token_123"
