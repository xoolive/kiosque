from __future__ import annotations

import asyncio
import logging
import re
import webbrowser
from typing import ClassVar

import pyperclip
from rich.text import Text
from textual import events, on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.logging import TextualHandler
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    MarkdownViewer,
    Static,
    TabbedContent,
    TabPane,
)

from kiosque.api.github import GitHubAPI, GitHubRepo
from kiosque.api.raindrop import RaindropAPI, RaindropItem
from kiosque.core.config import (
    validate_github_config,
    validate_raindrop_config,
    validate_tui_config,
)
from kiosque.core.website import Website

logging.basicConfig(handlers=[TextualHandler()])


class TextDisplay(Static):
    def __init__(self, text, id=None, **kwargs):
        self.text = text
        self.kwargs = kwargs
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        yield Static(Text(self.text, **self.kwargs))


class SearchBar(Input):
    BINDINGS = [  # noqa: RUF012
        Binding("c-c", "clear", show=False),
        Binding("escape", "clear", show=False),
    ]

    async def action_clear(self) -> None:
        self.clear()
        # Get the active tab's container
        try:
            tabbed = self.app.query_one(TabbedContent)
            active_pane = tabbed.get_child_by_id(tabbed.active)
            container = active_pane.query_one(VerticalScroll)
            for child in container.children:
                child.focus()
                break
        except Exception:
            # Fallback for non-tabbed layout
            container = self.app.query_one(VerticalScroll)
            for child in container.children:
                child.focus()
                break


class MarkdownModalScreen(ModalScreen):
    BINDINGS: ClassVar = [Binding("space", "close", "Close preview")]

    def __init__(self, markdown_text: str, **kwargs):
        self.markdown_text = markdown_text
        # Parse YAML frontmatter if present
        self.metadata = {}
        self.content = markdown_text

        if markdown_text.startswith("---\n"):
            parts = markdown_text.split("---\n", 2)
            if len(parts) >= 3:
                # Extract metadata from frontmatter
                frontmatter = parts[1]
                for line in frontmatter.strip().split("\n"):
                    if ": " in line:
                        key, value = line.split(": ", 1)
                        self.metadata[key.strip()] = value.strip()
                # Content is everything after the second ---
                self.content = parts[2].strip()

        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        # If we have metadata, display it nicely above the content
        if self.metadata:
            # Build a nice header with metadata
            header_lines = []
            if "title" in self.metadata:
                header_lines.append(f"# {self.metadata['title']}\n")
            if "author" in self.metadata:
                header_lines.append(f"**By {self.metadata['author']}**")
            if "date" in self.metadata:
                header_lines.append(f" · {self.metadata['date']}")
            if "author" in self.metadata or "date" in self.metadata:
                header_lines.append("\n\n")
            if "description" in self.metadata:
                header_lines.append(f"*{self.metadata['description']}*\n\n")
            if "url" in self.metadata:
                header_lines.append("---\n\n")

            formatted_content = "".join(header_lines) + self.content
            yield MarkdownViewer(
                formatted_content, show_table_of_contents=False
            )
        else:
            yield MarkdownViewer(
                self.markdown_text, show_table_of_contents=False
            )

    def action_close(self):
        self.dismiss()


class Entry(Button):
    """Entry for Raindrop.io bookmarks."""

    BINDINGS = [  # noqa: RUF012
        Binding("o,enter", "enter", "Open in browser", show=False),
        ("c", "copy", "Copy URL"),
        ("d", "delete", "Delete"),
        ("e", "archive", "Archive"),
        Binding("space", "preview", "Preview"),
    ]

    def __init__(self, elt: RaindropItem):
        self.title = elt.title
        self.url = str(elt.link)
        self.added = elt.created
        self.excerpt = elt.excerpt
        self.tags = elt.tags
        self.item_id = elt.id_
        super().__init__()

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

    def compose(self) -> ComposeResult:
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
        # Title line: repo name + date
        yield Horizontal(
            TextDisplay(self.title, id="title", overflow="ellipsis"),
            TextDisplay(f"{self.added:%d %b %y}", id="date"),
            id="entrytitle",
        )
        # Language and stars (on same line as tags, but separate for now)
        lang_stars = f"{self.language}" if self.language else ""
        if lang_stars and self.stars:
            lang_stars += f" · ⭐ {self.stars}"
        elif self.stars:
            lang_stars = f"⭐ {self.stars}"

        # Topics/tags with # prefix - same ID as Raindrop for styling
        if self.topics:
            topics_str = " ".join(
                f"#{topic}" for topic in self.topics[:3]
            )  # Limit to 3 topics
            if lang_stars:
                yield TextDisplay(f"{lang_stars} · {topics_str}", id="tags")
            else:
                yield TextDisplay(topics_str, id="tags")
        elif lang_stars:
            yield TextDisplay(lang_stars, id="tags")
        else:
            yield TextDisplay("", id="tags")

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


class Kiosque(App):
    CSS_PATH = "kiosque.tcss"
    BINDINGS = [  # noqa: RUF012
        ("q", "quit", "Quit"),
        Binding("/", "search", "Search"),
        Binding("g", "top", "Top", show=False),
        Binding("G", "bottom", "Bottom", show=False),
        Binding("j", "down", "Down", show=False),
        Binding("k", "up", "Up", show=False),
        Binding("ctrl+d", "down(5)", "Down by 5", show=False),
        Binding("ctrl+u", "up(5)", "Up by 5", show=False),
        ("r", "refresh", "Refresh"),
        Binding("1", "switch_tab('raindrop-tab')", "Raindrop", show=False),
        Binding("2", "switch_tab('github-tab')", "GitHub", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.raindrop_client: RaindropAPI | None = None
        self.github_client: GitHubAPI | None = None
        self.has_raindrop = False
        self.has_github = False
        self._search_timer: asyncio.TimerHandle | None = None

    def on_load(self, event: events.Load) -> None:
        """Sent before going in to application mode."""
        # Check which services are configured
        raindrop_config = validate_raindrop_config()
        github_config = validate_github_config()

        if raindrop_config:
            self.raindrop_client = RaindropAPI()
            self.has_raindrop = True

        if github_config:
            self.github_client = GitHubAPI()
            self.has_github = True

        if not self.has_raindrop and not self.has_github:
            raise RuntimeError(
                "No bookmark services configured. "
                "Please configure Raindrop.io or GitHub in kiosque.conf."
            )

    def action_search(self) -> None:
        self.query_one(Input).focus()

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to the specified tab."""
        try:
            tabbed = self.query_one(TabbedContent)
            tabbed.active = tab_id
        except Exception:
            pass

    @on(Input.Changed)
    def schedule_filter(self) -> None:
        """Schedule filter with debouncing - 300ms after last keystroke."""
        # Cancel any existing timer
        if self._search_timer is not None:
            self._search_timer.cancel()

        # Schedule new filter execution after 300ms
        loop = asyncio.get_event_loop()
        self._search_timer = loop.call_later(0.3, self.filter_items)

    def filter_items(self) -> None:
        search_key = self.query_one(Input).value

        # Filter in all containers (both tabs if present)
        containers = []
        try:
            # Try tabbed layout
            if self.has_raindrop:
                pane = self.query_one("#raindrop-tab")
                containers.append(pane.query_one(VerticalScroll))
            if self.has_github:
                pane = self.query_one("#github-tab")
                containers.append(pane.query_one(VerticalScroll))
        except Exception:
            # Fallback for non-tabbed layout
            try:
                containers.append(self.query_one(VerticalScroll))
            except Exception:
                return

        # Apply filter to all containers
        for container in containers:
            for entry in container.children:
                if isinstance(entry, (Entry, GitHubEntry)):
                    if entry.match(search_key):
                        entry.remove_class("hidden")
                    else:
                        entry.add_class("hidden")

    async def on_mount(self) -> None:
        # Progressive loading: render UI immediately, then load data
        # Load Raindrop first (faster), then GitHub (slower)
        if self.has_raindrop:
            # Load Raindrop immediately to give user quick feedback
            self._raindrop_task = asyncio.create_task(self._refresh_raindrop())

        if self.has_github:
            # Load GitHub after a small delay to not block Raindrop
            self._github_task = asyncio.create_task(
                self._delayed_github_refresh()
            )

        # Set up auto-refresh timer
        tui_config = validate_tui_config()
        self.timer = self.set_interval(
            tui_config.refresh_interval, self.action_refresh
        )

    async def _delayed_github_refresh(self) -> None:
        """Load GitHub stars with a small delay to prioritize Raindrop."""
        await asyncio.sleep(0.1)  # Small delay to let Raindrop render first
        await self._refresh_github()

    async def delete_raindrop(self, entry: Entry) -> None:
        """Delete a Raindrop entry."""
        if not self.raindrop_client:
            return
        c = await self.raindrop_client.async_client.delete(
            f"https://api.raindrop.io/rest/v1/raindrop/{entry.item_id}"
        )
        c.raise_for_status
        entry.remove()
        self.update_counts()

    async def archive_raindrop(self, entry: Entry) -> None:
        """Archive a Raindrop entry."""
        if not self.raindrop_client:
            return
        await self.raindrop_client.async_action("archive", entry.item_id)
        entry.remove()
        self.update_counts()

    async def unstar_repo(self, entry: GitHubEntry) -> None:
        """Unstar a GitHub repository."""
        if not self.github_client:
            return
        await self.github_client.unstar_repo_async(entry.owner, entry.repo_name)
        entry.remove()
        self.update_counts()

    async def preview_github_readme(self, entry: GitHubEntry) -> None:
        """Preview a GitHub repository's README."""
        if not self.github_client:
            return

        readme = await self.github_client.get_readme_async(
            entry.owner, entry.repo_name
        )
        if readme:
            # Add frontmatter for nice display
            frontmatter = f"""---
title: {entry.title}
description: {entry.description}
url: {entry.url}
---

"""
            modal = MarkdownModalScreen(frontmatter + readme)
            self.push_screen(modal)
        else:
            self.notify("No README found", severity="warning")

    def update_counts(self) -> None:
        """Update the title and tab labels with entry counts."""
        raindrop_count = 0
        github_count = 0

        try:
            if self.has_raindrop:
                try:
                    raindrop_pane = self.query_one("#raindrop-tab")
                    raindrop_container = raindrop_pane.query_one(VerticalScroll)
                    raindrop_count = len(raindrop_container.children)
                except Exception:
                    container = self.query_one("#raindrop-entries")
                    raindrop_count = len(container.children)

            if self.has_github:
                try:
                    github_pane = self.query_one("#github-tab")
                    github_container = github_pane.query_one(VerticalScroll)
                    github_count = len(github_container.children)
                except Exception:
                    container = self.query_one("#github-entries")
                    github_count = len(container.children)
        except Exception:
            pass

        # Update window title with counts
        total = raindrop_count + github_count
        title_parts = [f"Kiosque ({total})"]
        if raindrop_count > 0:
            title_parts.append(f"Raindrop ({raindrop_count})")
        if github_count > 0:
            title_parts.append(f"GitHub ({github_count})")
        self.title = " · ".join(title_parts)

    def compose(self) -> ComposeResult:
        yield Header()

        # Main content area with tabs
        with Container(id="main-content"):
            # Create tabs based on configured services
            if self.has_raindrop and self.has_github:
                with TabbedContent():
                    with TabPane("Raindrop", id="raindrop-tab"):
                        yield VerticalScroll(id="raindrop-entries")
                    with TabPane("GitHub", id="github-tab"):
                        yield VerticalScroll(id="github-entries")
            elif self.has_raindrop:
                yield VerticalScroll(id="raindrop-entries")
            elif self.has_github:
                yield VerticalScroll(id="github-entries")

        # Bottom bar with search and footer
        with Container(id="bottom-bar"):
            yield SearchBar(placeholder="Search...")
            yield Footer()

    def _get_active_container(self) -> VerticalScroll:
        """Get the currently active container."""
        try:
            tabbed = self.query_one(TabbedContent)
            active_pane = tabbed.get_child_by_id(tabbed.active)
            return active_pane.query_one(VerticalScroll)
        except Exception:
            # Fallback for non-tabbed layout
            return self.query_one(VerticalScroll)

    def action_up(self, by=1) -> None:
        container = self._get_active_container()
        for i, entry in enumerate(container.children):
            if entry.has_focus:
                break
        container.children[max(i - by, 0)].focus()

    def action_down(self, by=1) -> None:
        container = self._get_active_container()
        for i, entry in enumerate(container.children):
            if entry.has_focus:
                break
        container.children[min(i + by, len(container.children) - 1)].focus()

    def action_top(self) -> None:
        container = self._get_active_container()
        if len(container.children) > 0:
            container.children[0].focus()

    def action_bottom(self) -> None:
        container = self._get_active_container()
        if len(container.children) > 0:
            container.children[-1].focus()

    async def action_refresh(self, from_scratch=True) -> None:
        """Refresh all configured bookmark sources."""
        # Progressive loading: Raindrop first, then GitHub
        if self.has_raindrop:
            await self._refresh_raindrop()
        if self.has_github:
            await self._refresh_github()

    async def _refresh_raindrop(self) -> None:
        """Refresh Raindrop bookmarks."""
        if not self.raindrop_client:
            return

        try:
            pane = self.query_one("#raindrop-tab")
            container = pane.query_one(VerticalScroll)
        except Exception:
            container = self.query_one("#raindrop-entries")

        try:
            items = await self.raindrop_client.get_items_async()
        except Exception as exc:
            self.notify(
                f"Raindrop error: {exc}".replace("[", "").replace("]", "")
            )
            return

        new_entries = []
        for item in items:
            entry = Entry(item)
            if entry not in container.children:
                new_entries.append(entry)

        # Mount new entries at the beginning (most recent first)
        if new_entries and len(container.children) > 0:
            for entry in reversed(new_entries):
                await container.mount(entry, before=container.children[0])
        elif new_entries:
            for entry in new_entries:
                await container.mount(entry)

        # Update counts after loading
        self.update_counts()

    async def _refresh_github(self) -> None:
        """Refresh GitHub starred repositories."""
        if not self.github_client:
            return

        try:
            pane = self.query_one("#github-tab")
            container = pane.query_one(VerticalScroll)
        except Exception:
            container = self.query_one("#github-entries")

        try:
            repos = await self.github_client.get_all_starred_repos_async()
        except Exception as exc:
            self.notify(
                f"GitHub error: {exc}".replace("[", "").replace("]", "")
            )
            return

        # Sort by starred date (most recent first)
        repos.sort(key=lambda r: r.starred_at or r.created_at, reverse=True)

        new_entries = []
        for repo in repos:
            entry = GitHubEntry(repo)
            if entry not in container.children:
                new_entries.append(entry)

        # Mount new entries
        if new_entries and len(container.children) > 0:
            for entry in reversed(new_entries):
                await container.mount(entry, before=container.children[0])
        elif new_entries:
            for entry in new_entries:
                await container.mount(entry)

        if len(container.children) > 0 and not self.has_raindrop:
            # Only focus if there's no Raindrop tab (to avoid stealing focus)
            container.children[0].focus()

        # Update counts after loading
        self.update_counts()


def main() -> None:
    app = Kiosque()
    app.run()


if __name__ == "__main__":
    main()
