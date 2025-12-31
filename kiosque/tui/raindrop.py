"""Raindrop.io TUI components."""

from __future__ import annotations

import asyncio
import re
import webbrowser
from typing import TYPE_CHECKING

import pyperclip
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Button

from kiosque.api.raindrop import RaindropItem
from kiosque.core.website import Website

if TYPE_CHECKING:
    pass


class Entry(Button):
    """Entry for Raindrop.io bookmarks."""

    BINDINGS = [  # noqa: RUF012
        Binding("o,enter", "enter", "Open in browser", show=False),
        ("c", "copy", "Copy URL"),
        ("d", "delete", "Delete"),
        ("e", "archive", "Archive"),
        Binding("space", "preview", "Preview"),
        ("s", "star_github", "Star on GitHub"),
    ]

    def __init__(self, elt: RaindropItem):
        from .tui import parse_github_url

        self.title = elt.title
        self.url = str(elt.link)
        self.added = elt.created
        self.excerpt = elt.excerpt
        self.tags = elt.tags
        self.item_id = elt.id_
        self._github_repo: tuple[str, str] | None = None
        self._is_starred: bool | None = None
        super().__init__()

        # Check if this is a GitHub URL
        self._github_repo = parse_github_url(self.url)

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:
        """Check if an action is available.

        This controls both whether the action can be executed and whether
        it appears in the footer.
        """
        if action == "star_github":
            # Only enable/show for GitHub URLs when configured
            has_github = (
                hasattr(self.app, "github_client")
                and self.app.github_client is not None
            )
            return self._github_repo is not None and has_github
        return True

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Entry):
            return self.item_id == other.item_id
        return False

    def __hash__(self) -> int:
        return self.item_id

    def match(self, pattern: str) -> bool:
        if pattern == "":
            return True
        if next(re.finditer(pattern, self.title, re.IGNORECASE), None):
            return True
        if next(re.finditer(pattern, self.url, re.IGNORECASE), None):
            return True
        return False

    def on_focus(self) -> None:
        """Refresh bindings when entry gets focus to update footer."""
        self.refresh_bindings()

    def compose(self) -> ComposeResult:
        from .tui import TextDisplay

        yield Horizontal(
            TextDisplay(self.title, id="title", overflow="ellipsis"),
            TextDisplay(f"{self.added:%d %b %y}", id="date"),
            id="entrytitle",
        )
        yield TextDisplay(
            f"#{', #'.join(self.tags)}" if len(self.tags) else "", id="tags"
        )
        yield TextDisplay(self.url, id="url", overflow="ellipsis")
        yield TextDisplay(self.excerpt, id="excerpt")

    def action_copy(self) -> None:
        pyperclip.copy(self.url)

    def action_enter(self) -> None:
        webbrowser.open(self.url)

    async def action_archive(self) -> None:
        self.notify(f"Archive entry {self.item_id}")
        self.add_class("fading")
        self.app.screen.focus_next()
        await self.app.archive_raindrop(self)  # type: ignore

    async def action_delete(self) -> None:
        self.notify(f"Delete entry {self.item_id}")
        self.add_class("fading")
        self.app.screen.focus_next()
        await self.app.delete_raindrop(self)  # type: ignore

    async def action_preview(self) -> None:
        from .tui import MarkdownModalScreen

        # Check if this is a GitHub repo and we have a GitHub client
        if (
            self._github_repo
            and hasattr(self.app, "github_client")
            and self.app.github_client
        ):  # type: ignore
            owner, repo = self._github_repo
            self.notify("Loading GitHub README...")
            try:
                # Get README content from GitHub API
                readme = await self.app.github_client.get_readme_async(
                    owner, repo
                )  # type: ignore
                if readme:
                    # Add frontmatter for nice display
                    frontmatter = f"""---
title: {self.title}
description: {owner}/{repo}
url: {self.url}
---

"""
                    modal = MarkdownModalScreen(frontmatter + readme)
                    self.app.push_screen(modal)
                else:
                    self.notify("No README found", severity="warning")
                return
            except Exception as e:
                self.notify(
                    f"Error loading GitHub README: {e}", severity="error"
                )
                return

        # Fall back to website preview
        try:
            instance = Website.instance(self.url)
        except ValueError:
            self.notify("No preview available", severity="warning")
            return

        self.notify("Loading preview...")

        try:
            # Run sync full_text in thread pool to avoid blocking
            content_markdown = await asyncio.to_thread(
                instance.full_text, self.url
            )
            modal = MarkdownModalScreen(content_markdown)
            self.app.push_screen(modal)
        except Exception as e:
            self.notify(f"Error loading preview: {e}", severity="error")

    async def action_star_github(self) -> None:
        """Star a GitHub repository (only shown for GitHub URLs)."""
        if not self._github_repo:
            return

        if not hasattr(self.app, "github_client") or not self.app.github_client:  # type: ignore
            self.notify("GitHub not configured", severity="warning")
            return

        owner, repo = self._github_repo

        # Show immediate feedback with real delay to allow rendering
        self.notify(f"Checking {owner}/{repo}...")
        await asyncio.sleep(0.1)  # Small real delay for UI rendering

        # Check if already starred
        if self._is_starred is None:
            try:
                self._is_starred = (
                    await self.app.github_client.is_starred_async(owner, repo)
                )  # type: ignore
            except Exception:
                self._is_starred = False

        if self._is_starred:
            self.notify(
                f"{owner}/{repo} already starred", severity="information"
            )
            return

        # Star the repository
        self.notify(f"Starring {owner}/{repo}...")
        await asyncio.sleep(0.1)  # Small real delay for UI rendering

        try:
            await self.app.github_client.star_repo_async(owner, repo)  # type: ignore
            self._is_starred = True
            self.notify(f"⭐ Starred {owner}/{repo}")
            await asyncio.sleep(0.1)  # Small real delay for UI rendering

            # Refresh GitHub tab if it exists
            await self.app._refresh_github()  # type: ignore
            self.app.update_counts()  # type: ignore

            self.notify("✓ GitHub tab updated")
        except Exception as e:
            self.notify(f"Error starring repository: {e}", severity="error")
