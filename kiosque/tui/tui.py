from __future__ import annotations

import logging
import re
import webbrowser

import pandas as pd
import pyperclip
from rich.text import Text
from textual import events, on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.logging import TextualHandler
from textual.widgets import Button, Footer, Header, Input, Static

from kiosque.api.pocket import PocketAPI, PocketRetrieveEntry

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
        Binding("escape", "clear", show=False)
    ]

    async def action_clear(self) -> None:
        self.clear()
        container = self.app.query_one(VerticalScroll)
        for child in container.children:
            child.focus()
            break


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

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Entry):
            return self.item_id == other.item_id
        return False

    def __hash__(self) -> int:
        return int(self.item_id)

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
        await self.app.archive(self)  # type: ignore

    async def action_delete(self) -> None:
        self.notify(f"Delete entry {self.item_id}")
        self.add_class("fading")
        self.app.screen.focus_next()
        await self.app.delete(self)  # type: ignore


class Kiosque(App):
    CSS_PATH = "kiosque.css"
    BINDINGS = [  # noqa: RUF012
        ("q,escape", "quit", "Quit"),
        Binding("/", "search", "Search"),
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

    def action_search(self) -> None:
        self.query_one(Input).focus()

    @on(Input.Changed)
    def filter_items(self) -> None:
        container = self.query_one(VerticalScroll)
        search_key = self.query_one(Input).value
        for entry in container.children:
            if isinstance(entry, Entry):
                if entry.match(search_key):
                    entry.remove_class("hidden")
                else:
                    entry.add_class("hidden")

    async def on_mount(self) -> None:
        await self.action_refresh()
        self.timer = self.set_interval(3600, self.action_refresh)

    async def retrieve(self) -> list[Entry]:
        json = await self.pocket.async_retrieve()
        entries = list(Entry(elt) for elt in json["list"].values())
        self.title = f"Kiosque ({len(entries)})"
        return entries

    async def delete(self, entry: Entry) -> None:
        container = self.query_one(VerticalScroll)
        await self.pocket.async_action("delete", entry.item_id)
        entry.remove()
        self.title = f"Kiosque ({len(container.children)})"

    async def archive(self, entry: Entry) -> None:
        container = self.query_one(VerticalScroll)
        await self.pocket.async_action("archive", entry.item_id)
        entry.remove()
        self.title = f"Kiosque ({len(container.children)})"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield SearchBar(placeholder="Search...")
        yield VerticalScroll(id="entries")

    def action_up(self, by=1) -> None:
        container = self.query_one(VerticalScroll)
        for i, entry in enumerate(container.children):
            if entry.has_focus:
                break
        container.children[max(i - by, 0)].focus()

    def action_down(self, by=1) -> None:
        container = self.query_one(VerticalScroll)
        for i, entry in enumerate(container.children):
            if entry.has_focus:
                break
        container.children[min(i + by, len(container.children) - 1)].focus()

    def action_top(self) -> None:
        container = self.query_one(VerticalScroll)
        if len(container.children) > 0:
            container.children[0].focus()

    def action_bottom(self) -> None:
        container = self.query_one(VerticalScroll)
        if len(container.children) > 0:
            container.children[-1].focus()

    async def action_refresh(self) -> None:
        container = self.query_one(VerticalScroll)
        try:
            new_entries = await self.retrieve()
        except Exception:
            return
        for entry in container.children:
            if entry not in new_entries:
                entry.remove()
        if len(container.children) == 0:
            for entry in new_entries:
                await container.mount(entry)
            container.children[0].focus()
        else:
            n = sum(1 for e in new_entries if e not in container.children)
            self.notify(f"Adding {n} entries")
            for entry in new_entries[::-1]:
                if entry not in container.children:
                    await container.mount(entry, before=container.children[0])
                    entry.focus()


def main() -> None:
    app = Kiosque()
    app.run()


if __name__ == "__main__":
    main()
