"""GitHub TUI components."""

from __future__ import annotations

import re
import webbrowser
from typing import TYPE_CHECKING

import pyperclip
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Button

from kiosque.api.github import GitHubRepo

if TYPE_CHECKING:
    pass


class GitHubEntry(Button):
    """Entry for GitHub starred repositories."""

    BINDINGS = [  # noqa: RUF012
        Binding("o,enter", "enter", "Open in browser", show=False),
        ("c", "copy", "Copy URL"),
        ("u", "unstar", "Unstar"),
        Binding("space", "preview", "Preview README"),
    ]

    def __init__(self, repo: GitHubRepo):
        self.title = repo.full_name
        self.url = str(repo.html_url)
        self.description = repo.description or ""
        self.language = repo.language or ""
        self.stars = repo.stargazers_count
        self.topics = repo.topics
        self.added = repo.starred_at or repo.created_at
        self.repo_id = repo.id
        self.owner = repo.full_name.split("/")[0]
        self.repo_name = repo.full_name.split("/")[1]
        super().__init__()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, GitHubEntry):
            return self.repo_id == other.repo_id
        return False

    def __hash__(self) -> int:
        return self.repo_id

    def match(self, pattern: str) -> bool:
        if pattern == "":
            return True
        if next(re.finditer(pattern, self.title, re.IGNORECASE), None):
            return True
        if next(re.finditer(pattern, self.description, re.IGNORECASE), None):
            return True
        if self.language and next(
            re.finditer(pattern, self.language, re.IGNORECASE), None
        ):
            return True
        # Search in topics/tags
        for topic in self.topics:
            if next(re.finditer(pattern, topic, re.IGNORECASE), None):
                return True
        return False

    def compose(self) -> ComposeResult:
        from rich.text import Text

        from .tui import TextDisplay

        # Title line: repo name + date
        yield Horizontal(
            TextDisplay(self.title, id="title", overflow="ellipsis"),
            TextDisplay(f"{self.added:%d %b %y}", id="date"),
            id="entrytitle",
        )

        # Language and stars line with Rich Text markup for colors
        lang_stars = f"{self.language}" if self.language else ""
        if lang_stars and self.stars:
            lang_stars += f" · ⭐ {self.stars}"
        elif self.stars:
            lang_stars = f"⭐ {self.stars}"

        # Topics/tags with # prefix
        topics_str = ""
        if self.topics:
            topics_str = " · " + " ".join(
                f"#{topic}" for topic in self.topics[:3]
            )

        # Create Rich Text with different colors for lang/stars and tags
        combined_text = Text()
        if lang_stars:
            combined_text.append(lang_stars, style="#4c78ae")  # Blue
        if topics_str:
            combined_text.append(
                topics_str, style="italic #79806e"
            )  # Gray italic

        # Yield as single Static widget with Rich Text
        from textual.widgets import Static

        yield Static(combined_text, id="langstarstags")

        # Description
        yield TextDisplay(self.description, id="excerpt")

    def action_copy(self) -> None:
        pyperclip.copy(self.url)

    def action_enter(self) -> None:
        webbrowser.open(self.url)

    async def action_unstar(self) -> None:
        self.notify(f"Unstar {self.title}")
        self.add_class("fading")
        self.app.screen.focus_next()
        await self.app.unstar_repo(self)  # type: ignore

    async def action_preview(self) -> None:
        self.notify("Loading README...")
        try:
            await self.app.preview_github_readme(self)  # type: ignore
        except Exception as e:
            self.notify(f"Error loading README: {e}", severity="error")
