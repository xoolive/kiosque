from __future__ import annotations

import webbrowser
from dataclasses import dataclass, field

import pandas as pd
import pyperclip

# -- Rich imports --
from rich.console import Console, ConsoleOptions, RenderableType, RenderResult
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table

# -- Textual imports --
from textual import events
from textual.app import App
from textual.keys import Keys
from textual.reactive import Reactive
from textual.widget import Widget
from textual.widgets import Footer, Header, ScrollView

from ..api.pocket import PocketAPI


@dataclass
class Entry:
    item_id: str
    title: str
    url: str
    added: pd.Timestamp
    excerpt: str
    selected: bool = field(default=False)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        content_table = Table.grid(padding=(0, 1), expand=True)

        content_table.add_column("title", justify="left", ratio=1, no_wrap=True)
        content_table.add_column("date", justify="right", width=8)

        content_table.add_row(
            self.title,
            f"{self.added:%d %b %y}",
            style="yellow" if self.selected else "default",
        )
        content_table.add_row(self.url, style="blue")

        yield Panel(
            content_table,
            height=4,
            border_style="yellow" if self.selected else "default",
        )


@dataclass
class Entries:
    entries: list[Entry]

    def __len__(self):
        return len(self.entries)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield from self.entries


class BookmarksWidget(Widget):

    selected_index: Reactive[int] = Reactive(0)

    def __init__(self, name: str | None, pocket: PocketAPI) -> None:
        super().__init__(name=name)
        self.pocket = pocket
        entries = list(
            Entry(
                item_id=elt["item_id"],
                title=elt.get("resolved_title", elt["given_title"]),
                url=elt.get("resolved_url", elt["given_url"]),
                added=pd.Timestamp(int(elt.get("time_added")), unit="s"),
                excerpt=elt.get("excerpt", ""),
            )
            for elt in self.pocket
        )
        self.entries = Entries(entries)
        self.entries.entries[self.selected_index].selected = True

    def render(self) -> RenderableType:
        return Padding(self.entries)

    def action_up(self):
        self.entries.entries[self.selected_index].selected = False
        self.selected_index = max(self.selected_index - 1, 0)
        self.entries.entries[self.selected_index].selected = True

    def action_down(self):
        self.entries.entries[self.selected_index].selected = False
        self.selected_index = min(
            self.selected_index + 1, len(self.entries) - 1
        )
        self.entries.entries[self.selected_index].selected = True

    def action_copy(self):
        pyperclip.copy(self.entries.entries[self.selected_index].url)

    def action_enter(self):
        webbrowser.open(self.entries.entries[self.selected_index].url)


class Kiosque(App):
    async def on_load(self, event: events.Load) -> None:
        """Sent before going in to application mode."""

        # Bind our basic keys
        await self.bind("q", "quit", "Quit")
        await self.bind("escape", "quit", show=False)
        await self.bind("j, down", "down()", show=False)
        await self.bind("k, up", "up()", show=False)
        await self.bind("o", "enter()", "Open")
        await self.bind(Keys.Enter, "enter()", show=False)
        await self.bind("c", "copy", "Copy URL")

        self.pocket = PocketAPI()
        self.bookmarks = BookmarksWidget(name="bookmarks", pocket=self.pocket)
        self.excerpt = Markdown("**b**" * 200)

        self.bookmarkview = ScrollView(self.bookmarks)
        self.preview = ScrollView(self.excerpt)

    async def on_mount(self, event: events.Mount) -> None:
        """Call after terminal goes in to application mode"""

        # Dock our widgets
        await self.view.dock(Header(), edge="top")
        await self.view.dock(Footer(), edge="bottom")
        await self.view.dock(self.bookmarkview, self.preview, edge="top")

    async def action_up(self) -> None:
        self.bookmarks.action_up()
        self.refresh()

    async def action_down(self) -> None:
        self.bookmarks.action_down()
        self.refresh()

    async def action_copy(self) -> None:
        self.bookmarks.action_copy()

    async def action_enter(self) -> None:
        self.bookmarks.action_enter()


def main():
    Kiosque.run(title="Kiosque", log="kiosque.log")


if __name__ == "__main__":
    main()
