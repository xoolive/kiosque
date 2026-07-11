"""Tests for resolving PDF issue names without downloading their bodies."""

from typing import ClassVar
from unittest.mock import Mock, patch

from click.testing import CliRunner

import kiosque
from kiosque.core.website import Website


class ResolvableWebsite(Website):
    base_url = "https://issues.example.com/"
    login_url = "https://issues.example.com/login"
    alias: ClassVar = ["issues"]
    connected = True

    def latest_issue_url(self) -> str:
        return "https://issues.example.com/archive/h1234"


def test_resolve_latest_issue_streams_headers_only():
    response = Mock()
    response.raise_for_status = Mock()
    context = Mock()
    context.__enter__ = Mock(return_value=response)
    context.__exit__ = Mock(return_value=False)

    with patch(
        "kiosque.core.website.client.stream", return_value=context
    ) as stream:
        assert ResolvableWebsite().resolve_latest_issue() == "h1234.pdf"

    stream.assert_called_once_with(
        "GET", "https://issues.example.com/archive/h1234"
    )
    response.raise_for_status.assert_called_once_with()


def test_cli_resolve_prints_filename(monkeypatch):
    monkeypatch.setattr(
        kiosque,
        "config_dict",
        {"https://issues.example.com/": {"alias": "issues"}},
    )
    monkeypatch.setattr(
        kiosque.Website,
        "instance",
        Mock(return_value=ResolvableWebsite()),
    )
    monkeypatch.setattr(
        ResolvableWebsite,
        "resolve_latest_issue",
        Mock(return_value="h1234.pdf"),
    )

    result = CliRunner().invoke(kiosque.main, ["issues", "--resolve"])

    assert result.exit_code == 0
    assert result.output == "h1234.pdf\n"


def test_cli_resolve_requires_alias():
    result = CliRunner().invoke(kiosque.main, ["--resolve"])

    assert result.exit_code == 2
    assert "--resolve requires a publication alias" in result.output
