"""Media format picker; downloads remain owned by the application."""

from __future__ import annotations

import asyncio
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import ClassVar

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Footer, Label, Select, SelectionList, Static

from kiosque.core.media import DownloadSelection, MediaInfo, MediaService


@dataclass
class MediaDownload:
    url: str
    selection: DownloadSelection
    status: str = "Starting…"
    cancel: threading.Event = field(default_factory=threading.Event)
    done: bool = False


class MediaModalScreen(ModalScreen[None]):
    """Space/Escape close; Enter selects subtitles; downloads keep running."""

    BINDINGS: ClassVar = [
        Binding("ctrl+s", "download", "Download"),
        Binding("r", "refresh", "Refresh"),
        Binding("x", "cancel", "Cancel job"),
        Binding("space", "close", "Close", priority=True),
        Binding("escape", "close", "Close", show=False),
    ]

    def __init__(
        self,
        url: str,
        service: MediaService,
        jobs: list[MediaDownload],
        start_download: Callable[[str, DownloadSelection], MediaDownload],
    ) -> None:
        super().__init__()
        self.url = url
        self.service = service
        self.jobs = jobs
        self.start_download = start_download
        self.info: MediaInfo | None = None
        self._selection_error: str | None = None
        self._action_state: tuple[bool, bool] | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="media-panel"):
            with VerticalScroll(id="media-form"):
                yield Static("Loading media…", id="media-title", markup=False)
                yield Static(self.url, id="media-url", markup=False)
                yield Static(
                    f"Download to: {self.service.config.download_dir}",
                    id="media-destination",
                    markup=False,
                )
                yield Static(
                    "Discovering formats…", id="media-cache", markup=False
                )
                yield Label("Video / version")
                # Type-to-search would consume Space in an expanded dropdown,
                # masking even the screen's priority close binding.
                yield Select[str](
                    [("No video (audio / subtitles only)", "none")],
                    value="none",
                    allow_blank=False,
                    type_to_search=False,
                    disabled=True,
                    id="media-video",
                )
                yield Label("Audio (combined videos keep their own audio)")
                yield Select[str](
                    [
                        ("Automatic matching audio", "auto"),
                        ("No audio", "none"),
                    ],
                    value="auto",
                    allow_blank=False,
                    type_to_search=False,
                    disabled=True,
                    id="media-audio",
                )
                yield Label(
                    "Subtitles — Enter or click toggles; Space closes preview"
                )
                yield SelectionList[str](id="media-subtitles", disabled=True)
                yield Static(
                    "Audio-only: choose No video and an audio version. "
                    "Subtitles-only: choose No video and No audio. "
                    "Separate video/audio tracks merge into MKV without "
                    "re-encoding; subtitles are saved as sidecar files.",
                    id="media-help",
                    markup=False,
                )
            yield Static("", id="media-progress", markup=False)
            yield Footer(id="media-footer")

    def on_mount(self) -> None:
        self.set_interval(0.2, self.update_progress)
        self._load()

    def _load(self, *, force: bool = False) -> None:
        self.run_worker(
            self.load_formats(force=force),
            group="media-discovery",
            exclusive=True,
            exit_on_error=False,
        )

    async def load_formats(self, *, force: bool = False) -> None:
        status = self.query_one("#media-cache", Static)
        if not force:
            cached = await asyncio.to_thread(self.service.cached, self.url)
            if cached:
                self.apply_info(cached)
                age = max(0, int((time.time() - cached.fetched_at) / 60))
                status.update(f"Cached formats · {age} min old")
                if self.service.is_fresh(cached):
                    return
                status.update(f"Cached formats · {age} min old · refreshing…")
        else:
            status.update("Refreshing formats…")
        try:
            info = await self.service.discover(self.url, force=force)
            if self.apply_info(info, preserve=not force):
                status.update("Formats updated just now · r to refresh")
            else:
                status.update(
                    "Available tracks changed. Press r to reload choices; "
                    "your current selection has been kept."
                )
        except Exception as exc:
            prefix = (
                "Refresh failed; cached choices retained"
                if self.info
                else "No media preview"
            )
            status.update(f"{prefix}: {exc}")

    def apply_info(self, info: MediaInfo, *, preserve: bool = False) -> bool:
        video = self.query_one("#media-video", Select)
        audio = self.query_one("#media-audio", Select)
        subtitles = self.query_one("#media-subtitles", SelectionList)
        videos = [fmt for fmt in reversed(info.formats) if fmt.has_video]
        audios = [fmt for fmt in reversed(info.formats) if fmt.has_audio]
        video_options = [(Text("No video (audio / subtitles only)"), "none")]
        video_options += [(Text(fmt.label), f"f:{fmt.id}") for fmt in videos]
        audio_options = [
            (Text("Automatic matching audio"), "auto"),
            (Text("No audio"), "none"),
        ]
        audio_options += [
            (
                Text(
                    f"{'Extract audio · ' if fmt.has_video else ''}{fmt.label}"
                ),
                f"f:{fmt.id}",
            )
            for fmt in audios
        ]
        selected = list(subtitles.selected) if self.info and preserve else []
        chosen_video = (
            video.value
            if self.info and preserve
            else (f"f:{videos[0].id}" if videos else "none")
        )
        chosen_audio = (
            audio.value
            if self.info and preserve
            else ("auto" if audios else "none")
        )
        if preserve and self.info:
            if (
                chosen_video not in {value for _, value in video_options}
                or chosen_audio not in {value for _, value in audio_options}
                or not set(selected).issubset(
                    {track.key for track in info.subtitles}
                )
            ):
                return False
        video.set_options(video_options)
        video.value = chosen_video
        audio.set_options(audio_options)
        audio.value = chosen_audio
        subtitles.clear_options()
        subtitles.add_options(
            [
                (Text(track.label), track.key, track.key in selected)
                for track in info.subtitles
            ]
        )
        subtitles.highlighted = 0 if info.subtitles else None
        video.disabled = audio.disabled = False
        subtitles.disabled = not info.subtitles
        self.info = info
        self.query_one("#media-title", Static).update(info.title)
        self.update_progress()
        return True

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:
        """Keep unavailable footer actions visible but dimmed and inactive."""
        active = next(
            (
                job
                for job in reversed(self.jobs)
                if job.url == self.url and not job.done
            ),
            None,
        )
        if action == "download" and (self.info is None or active is not None):
            return None
        if action == "cancel" and (active is None or active.cancel.is_set()):
            return None
        return True

    def update_progress(self) -> None:
        job = next(
            (job for job in reversed(self.jobs) if job.url == self.url), None
        )
        state = (
            self.check_action("download", ()) is True,
            self.check_action("cancel", ()) is True,
        )
        if state != self._action_state:
            self._action_state = state
            self.refresh_bindings()
        if job and not job.done:
            status = (
                "Cancellation requested…" if job.cancel.is_set() else job.status
            )
        else:
            status = self._selection_error or (job.status if job else "")
        self.query_one("#media-progress", Static).update(status)

    def action_download(self) -> None:
        if self.check_action("download", ()) is not True or self.info is None:
            return
        video = self.query_one("#media-video", Select).value
        audio = self.query_one("#media-audio", Select).value
        selection = DownloadSelection(
            video=str(video)[2:] if str(video).startswith("f:") else None,
            audio=str(audio)[2:]
            if str(audio).startswith("f:")
            else ("auto" if audio == "auto" else None),
            subtitles=list(
                self.query_one("#media-subtitles", SelectionList).selected
            ),
        )
        try:
            self.service.download_options(self.info, selection)
        except Exception as exc:
            self._selection_error = str(exc)
            self.update_progress()
            return
        self._selection_error = None
        self.start_download(self.url, selection)
        self.update_progress()

    def action_refresh(self) -> None:
        self._load(force=True)

    def action_cancel(self) -> None:
        for job in self.jobs:
            if job.url == self.url and not job.done:
                job.cancel.set()
        self.update_progress()

    def action_close(self) -> None:
        self.dismiss()
