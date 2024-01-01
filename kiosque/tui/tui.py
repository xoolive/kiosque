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

from kiosque.api.pocket import PocketAPI, PocketRetrieveEntry


class TextDisplay(Static):
    def __init__(self, text, id=None, **kwargs):
        self.text = text
        self.kwargs = kwargs
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        yield Static(Text(self.text, **self.kwargs))


class Entry(Button):
    BINDINGS = [  # noqa: RUF012
        Binding("o,enter", "enter", "Open in browser", show=False),
        ("c", "copy", "Copy URL"),
        ("d", "delete", "Delete"),
        ("e", "archive", "Archive"),
    ]

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

    def action_copy(self) -> None:
        pyperclip.copy(self.url)

    def action_enter(self) -> None:
        webbrowser.open(self.url)

    async def action_archive(self) -> None:
        self.add_class("fading")
        self.app.screen.focus_next()
        await self.app.archive(self)  # type: ignore

    async def action_delete(self) -> None:
        self.add_class("fading")
        self.app.screen.focus_next()
        await self.app.delete(self)  # type: ignore


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
        ("r", "refresh", "Refresh"),
    ]

    def on_load(self, event: events.Load) -> None:
        """Sent before going in to application mode."""
        self.pocket = PocketAPI()
        self.entries: list[Entry] = []

    async def on_mount(self) -> None:
        # await self.action_refresh()
        self.timer = self.set_interval(60, self.action_refresh)

    async def retrieve(self) -> list[Entry]:
        json = await self.pocket.async_retrieve()
        self.entries = list(Entry(elt) for elt in json["list"].values())
        self.title = f"Kiosque ({len(self.entries)})"
        return self.entries

    async def delete(self, entry: Entry) -> None:
        await self.pocket.async_action("delete", entry.item_id)
        self.entries.remove(entry)
        self.title = f"Kiosque ({len(self.entries)})"
        entry.remove()

    async def archive(self, entry: Entry) -> None:
        await self.pocket.async_action("archive", entry.item_id)
        self.entries.remove(entry)
        self.title = f"Kiosque ({len(self.entries)})"
        entry.remove()

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

    def action_bottom(self) -> None:
        self.entries[-1].focus()

    async def action_refresh(self) -> None:
        container = self.query_one("#entries", VerticalScroll)
        for entry in self.entries:
            entry.remove()
        for entry in await self.retrieve():
            container.mount(entry)
        self.action_top()


def main() -> None:
    app = Kiosque()
    app.run()


if __name__ == "__main__":
    main()
