"""Regression tests for user-entered GitHub homepage values."""

import asyncio
from typing import Any

import httpx
import pytest

from kiosque.api.github import GitHubAPI, GitHubRepo


@pytest.fixture
def repo_data() -> dict[str, Any]:
    return {
        "id": 1,
        "name": "example",
        "full_name": "example/example",
        "html_url": "https://github.com/example/example",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "pushed_at": "2026-01-01T00:00:00Z",
        "owner": {"login": "example"},
    }


@pytest.mark.parametrize(
    ("homepage", "expected"),
    [
        (None, None),
        ("", None),
        ("   ", None),
        ("basalt.page", "https://basalt.page/"),
        (" example.org/docs ", "https://example.org/docs"),
        ("https://example.org", "https://example.org/"),
        ("http://example.org/docs", "http://example.org/docs"),
    ],
)
def test_homepage_normalization(repo_data, homepage, expected):
    repo = GitHubRepo.model_validate({**repo_data, "homepage": homepage})
    actual = str(repo.homepage) if repo.homepage is not None else None
    assert actual == expected


def test_homepage_can_be_omitted(repo_data):
    assert GitHubRepo.model_validate(repo_data).homepage is None


def test_starred_repo_refresh_accepts_scheme_less_homepages(repo_data):
    """One bare homepage must not prevent loading the entire GitHub tab."""
    homepages = ["https://example.org", "basalt.page", "   "]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/user/starred"
        assert request.headers["Accept"] == "application/vnd.github.star+json"
        return httpx.Response(
            200,
            json=[
                {
                    "starred_at": "2026-01-01T00:00:00Z",
                    "repo": {**repo_data, "id": index, "homepage": homepage},
                }
                for index, homepage in enumerate(homepages, start=1)
            ],
        )

    async def run():
        # Exercise response parsing without configuration or real credentials.
        api = GitHubAPI.__new__(GitHubAPI)
        api.headers = {}
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as client:
            api.async_client = client
            return await api.get_all_starred_repos_async()

    repos = asyncio.run(run())
    assert len(repos) == 3
    assert str(repos[1].homepage) == "https://basalt.page/"
    assert repos[2].homepage is None
