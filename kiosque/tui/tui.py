from __future__ import annotations

import webbrowser

import pandas as pd
import pyperclip
from rich.text import Text
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Footer, Header, Static

from ..api.pocket import PocketAPI, PocketRetrieveEntry


class TextDisplay(Static):
    def __init__(self, text, id=None, **kwargs):
        self.text = text
        self.kwargs = kwargs
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        yield Static(Text(self.text, **self.kwargs))


class Entry(Button):
    def __init__(self, elt: PocketRetrieveEntry):
        self.title = elt.get("resolved_title", elt["given_title"])
        self.url = elt.get("resolved_url", elt["given_url"])
        self.added = pd.Timestamp(int(elt["time_added"]), unit="s")
        self.excerpt = elt.get("excerpt", "")
        self.item_id = elt["item_id"]
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Horizontal(
            TextDisplay(self.title, id="title", overflow="ellipsis"),
            TextDisplay(f"{self.added:%d %b %y}", id="date"),
            id="entrytitle",
        )
        yield TextDisplay(self.url, id="url", overflow="ellipsis")
        yield TextDisplay(self.excerpt, id="excerpt")


class Kiosque(App):
    CSS_PATH = "kiosque.css"
    BINDINGS = [  # noqa: RUF012
        ("q,escape", "quit", "Quit"),
        Binding("g", "top", "Top", show=False),
        Binding("G", "bottom", "Bottom", show=False),
        Binding("j", "down", "Down", show=False),
        Binding("k", "up", "Up", show=False),
        Binding("ctrl+d", "down(5)", "Down by 5", show=False),
        Binding("ctrl+u", "up(5)", "Up by 5", show=False),
        Binding("o,enter", "enter", "Open in browser"),
        ("c", "copy", "Copy URL"),
        ("D", "delete", "Delete"),
        ("e", "archive", "Archive"),
        ("r", "refresh", "Refresh"),
        ("s", "save", "Save in file"),
    ]

    def on_load(self, event: events.Load) -> None:
        """Sent before going in to application mode."""
        self.pocket = PocketAPI()
        self.entries: list[Entry] = []

    async def on_mount(self) -> None:
        await self.action_refresh()

    async def retrieve(self) -> None:
        json = await self.pocket.async_retrieve()
        self.entries = list(Entry(elt) for elt in json["list"].values())

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield VerticalScroll(id="entries")

    def action_up(self, by=1) -> None:
        for i, entry in enumerate(self.entries):
            if entry.has_focus:
                break
        self.entries[max(i - by, 0)].focus()

    def action_down(self, by=1) -> None:
        for i, entry in enumerate(self.entries):
            if entry.has_focus:
                break
        self.entries[min(i + by, len(self.entries) - 1)].focus()

    def action_top(self) -> None:
        self.entries[0].focus()
        self.call_after_refresh(self.screen.scroll_end, animate=False)

    def action_bottom(self) -> None:
        self.entries[-1].focus()

    def action_copy(self) -> None:
        current = next(entry for entry in self.entries if entry.has_focus)
        pyperclip.copy(current.url if current is not None else "nothing")

    def action_enter(self) -> None:
        current = next(entry for entry in self.entries if entry.has_focus)
        webbrowser.open(current.url)

    async def action_archive(self) -> None:
        current = next(entry for entry in self.entries if entry.has_focus)
        await self.pocket.async_action("archive", current.item_id)
        current.remove()
        self.entries.remove(current)
        self.title = f"Kiosque ({len(self.entries)})"

    async def action_delete(self) -> None:
        current = next(entry for entry in self.entries if entry.has_focus)
        await self.pocket.async_action("delete", current.item_id)
        current.remove()
        self.entries.remove(current)
        self.title = f"Kiosque ({len(self.entries)})"

    async def action_refresh(self) -> None:
        for entry in self.entries:
            entry.remove()
        await self.retrieve()
        container = self.query_one("#entries")
        for entry in self.entries:
            container.mount(entry)
        self.action_top()
        self.title = f"Kiosque ({len(self.entries)})"

    def action_save(self) -> None:
        # Website.instance(url).write_text(url)
        pass


def main() -> None:
    app = Kiosque()
    app.run()


if __name__ == "__main__":
    main()
