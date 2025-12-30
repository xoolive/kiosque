"""Tests for website login functionality with real credentials from config.

NOTE: These tests make real HTTP requests to websites. Login mechanisms
may change over time, causing tests to fail. Failures often indicate
that the website's login flow has changed and needs updating in the
corresponding website implementation file.

These tests are marked with @pytest.mark.login and are skipped in CI.
Run locally with: pytest tests/test_login.py
"""

import pytest

from kiosque.core.config import config_dict
from kiosque.core.website import Website

# Websites with known broken/outdated login flows
# NOTE: Geo-blocked sites work with French/EU SOCKS/HTTP proxy configured
KNOWN_BROKEN_LOGINS = {
    # Geo-blocked login: Returns 406 on secure.courrierinternational.com
    # WORKS with French/EU proxy - configure [proxy] in kiosque.conf
    "https://www.courrierinternational.com/",
    # Geo-blocked: Returns 403 Forbidden (Akamai CDN)
    # WORKS with French/EU proxy - configure [proxy] in kiosque.conf
    "https://www.lesechos.fr/",
}


@pytest.mark.login
@pytest.mark.parametrize(
    "base_url", [url for url in config_dict.keys() if url.startswith("http")]
)
def test_website_login(base_url):
    """Test login to websites that have credentials configured.

    This test is parameterized to run for each website configured
    in kiosque.conf with credentials.
    """
    # Skip if no credentials configured
    if not config_dict.get(base_url):
        pytest.skip(f"No credentials configured for {base_url}")

    creds = config_dict[base_url]
    if not creds.get("username") or not creds.get("password"):
        pytest.skip(f"Incomplete credentials for {base_url}")

    # Mark as expected failure if login is known to be broken
    if base_url in KNOWN_BROKEN_LOGINS:
        pytest.xfail(
            f"Login for {base_url} is known to be broken/outdated. "
            "Website login flow may have changed."
        )

    # Get the website instance
    try:
        instance = Website.instance(base_url)
    except ValueError:
        pytest.skip(f"Website not supported: {base_url}")

    # Check that credentials were loaded
    assert instance.credentials is not None
    assert "username" in instance.credentials
    assert "password" in instance.credentials

    # Attempt login (this will actually make HTTP requests)
    # We don't verify the exact response, just that it doesn't crash
    try:
        response = instance.login()
        # If login_dict is empty, login() returns None (no auth needed)
        if response is not None:
            # Check that we got some response
            assert response is not None
            # The connected flag should be set
            assert instance.__class__.connected is True
    except Exception as e:
        pytest.fail(f"Login failed for {base_url}: {e}")


def test_no_credentials_skips_login():
    """Test that websites without credentials don't attempt login."""
    # Create a mock test website without trying to connect
    from unittest.mock import Mock, patch

    # Mock the httpx client to avoid actual HTTP calls
    with patch("kiosque.core.client.client") as mock_client:
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.post.return_value = mock_response

        class TestWebsite(Website):
            base_url = "https://test-no-creds.example.com/"
            login_url = "https://test-no-creds.example.com/login"

        instance = TestWebsite()
        assert instance.credentials is None

        # Login should return None for websites without credentials
        response = instance.login()
        assert response is None
        # Should have called get once (for the base_url check)
        assert mock_client.get.called
        # Should NOT have called post (no login attempted)
        assert not mock_client.post.called


def test_list_configured_websites():
    """Test that we can list all configured websites."""
    configured = [url for url in config_dict.keys() if url.startswith("http")]

    # Should have at least some configured (or skip if empty)
    if not configured:
        pytest.skip("No websites configured in kiosque.conf")

    print(f"\nConfigured websites ({len(configured)}):")
    for url in configured:
        creds = config_dict[url]
        has_username = bool(creds.get("username"))
        has_password = bool(creds.get("password"))
        status = "✓" if (has_username and has_password) else "✗"
        print(f"  {status} {url}")
