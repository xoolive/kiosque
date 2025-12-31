from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel, Field, HttpUrl, field_validator

from ..core.config import config_dict


class GitHubRepo(BaseModel):
    """Model representing a GitHub repository."""

    id: int
    name: str
    full_name: str
    html_url: HttpUrl
    description: str | None = None
    language: str | None = None
    stargazers_count: int = 0
    topics: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime
    homepage: HttpUrl | None = None
    owner: dict[str, Any]  # Contains login, avatar_url, etc.

    # Additional fields for starred repos
    starred_at: datetime | None = None

    @field_validator("homepage", mode="before")
    @classmethod
    def validate_homepage(cls, v: str | None) -> str | None:
        """Validate homepage URL, converting empty strings to None."""
        if v == "" or v is None:
            return None
        return v


class GitHubAPI:
    """API client for interacting with GitHub.

    Go to https://github.com/settings/tokens
    Create a classic token with 'public_repo' or 'repo' scope
    """

    def __init__(self) -> None:
        github_config = config_dict.get("github", None)
        assert github_config is not None, "GitHub configuration not found."

        self.token = github_config.get("token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.client = httpx.Client(headers=self.headers, timeout=30.0)
        self.async_client = httpx.AsyncClient(
            headers=self.headers, timeout=30.0
        )

    async def get_user_async(self) -> dict[str, Any]:
        """Get the authenticated user's information."""
        response = await self.async_client.get("https://api.github.com/user")
        response.raise_for_status()
        return response.json()

    async def get_starred_repos_async(
        self, page: int = 1, per_page: int = 100
    ) -> list[GitHubRepo]:
        """Get starred repositories for the authenticated user.

        Args:
            page: Page number (1-indexed)
            per_page: Number of results per page (max 100)

        Returns:
            List of GitHubRepo objects
        """
        # Use the star timestamp header to get when repos were starred
        headers = {
            **self.headers,
            "Accept": "application/vnd.github.star+json",
        }
        response = await self.async_client.get(
            "https://api.github.com/user/starred",
            params={"page": page, "per_page": per_page},
            headers=headers,
        )
        response.raise_for_status()

        repos = []
        for item in response.json():
            repo_data = item["repo"]
            repo_data["starred_at"] = item["starred_at"]
            repos.append(GitHubRepo(**repo_data))

        return repos

    async def get_all_starred_repos_async(self) -> list[GitHubRepo]:
        """Get all starred repositories (handles pagination automatically)."""
        all_repos = []
        page = 1

        while True:
            repos = await self.get_starred_repos_async(page=page, per_page=100)
            if not repos:
                break
            all_repos.extend(repos)
            if len(repos) < 100:  # Last page
                break
            page += 1

        return all_repos

    async def get_readme_async(self, owner: str, repo: str) -> str | None:
        """Get the README content for a repository.

        Args:
            owner: Repository owner (username or organization)
            repo: Repository name

        Returns:
            README content in markdown format, or None if not found
        """
        try:
            response = await self.async_client.get(
                f"https://api.github.com/repos/{owner}/{repo}/readme",
                headers={
                    **self.headers,
                    "Accept": "application/vnd.github.raw+json",
                },
            )
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None  # No README found
            raise

    async def get_languages_async(
        self, owner: str, repo: str
    ) -> dict[str, int]:
        """Get languages used in a repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Dictionary mapping language names to bytes of code
        """
        response = await self.async_client.get(
            f"https://api.github.com/repos/{owner}/{repo}/languages"
        )
        response.raise_for_status()
        return response.json()

    async def unstar_repo_async(self, owner: str, repo: str) -> None:
        """Unstar a repository.

        Args:
            owner: Repository owner
            repo: Repository name
        """
        response = await self.async_client.delete(
            f"https://api.github.com/user/starred/{owner}/{repo}"
        )
        response.raise_for_status()

    async def star_repo_async(self, owner: str, repo: str) -> None:
        """Star a repository.

        Args:
            owner: Repository owner
            repo: Repository name
        """
        response = await self.async_client.put(
            f"https://api.github.com/user/starred/{owner}/{repo}"
        )
        response.raise_for_status()

    async def is_starred_async(self, owner: str, repo: str) -> bool:
        """Check if a repository is starred.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            True if starred, False otherwise
        """
        response = await self.async_client.get(
            f"https://api.github.com/user/starred/{owner}/{repo}"
        )
        return response.status_code == 204

    async def async_retrieve(self, offset: int = 0) -> dict[str, Any]:
        """Legacy method for compatibility with TUI - returns formatted data.

        Args:
            offset: Offset for pagination (not used, GitHub API uses pages)

        Returns:
            Dict with 'list' (dict of repos by ID) and 'count'
        """
        repos = await self.get_all_starred_repos_async()

        # Convert to format expected by TUI
        items_dict = {str(repo.id): repo for repo in repos}
        return {"list": items_dict, "count": len(repos)}

    async def async_action(
        self, action: str, repo_id: int, owner: str, repo: str
    ) -> None:
        """Perform an action on a repository.

        Args:
            action: Action to perform ('unstar', etc.)
            repo_id: Repository ID (for compatibility)
            owner: Repository owner
            repo: Repository name
        """
        if action == "unstar":
            await self.unstar_repo_async(owner, repo)
        else:
            raise ValueError(f"Unknown action: {action}")

    def close(self) -> None:
        """Close HTTP clients."""
        self.client.close()
        self.async_client.close()

    async def aclose(self) -> None:
        """Async close HTTP clients."""
        await self.async_client.aclose()
        self.client.close()
