"""Headless Textual tests for media previews and app-owned downloads."""

import asyncio
import threading
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from textual.containers import VerticalScroll
from textual.widgets import (
    Button,
    Footer,
    MarkdownViewer,
    Select,
    SelectionList,
    Static,
)

from kiosque.api.raindrop import RaindropItem
from kiosque.core.config import MediaConfig
from kiosque.core.media import (
    DownloadCancelled,
    DownloadSelection,
    MediaFormat,
    MediaInfo,
    MediaService,
    SubtitleTrack,
)
from kiosque.tui.media import MediaDownload, MediaModalScreen
from kiosque.tui.raindrop import Entry
from kiosque.tui.tui import Kiosque, MarkdownModalScreen

URL = "https://www.youtube.com/watch?v=YE7VzlLtp-4"


class MediaTestApp(Kiosque):
    CSS_PATH = Path(__file__).parents[1] / "kiosque/tui/kiosque.tcss"

    def on_load(self, event) -> None:
        self.has_raindrop = True

    async def on_mount(self) -> None:
        pass


@pytest.fixture
def service(tmp_path):
    service = MediaService(
        MediaConfig(download_dir=tmp_path / "downloads"),
        cache_dir=tmp_path / "cache",
    )
    info = MediaInfo(
        id="example",
        title="Example [original]",
        formats=[
            MediaFormat(id="a", ext="m4a", acodec="aac"),
            MediaFormat(id="v", ext="mp4", vcodec="h264", acodec="aac"),
        ],
        subtitles=[SubtitleTrack(language="en", ext="vtt")],
    )
    service._store(URL, info)
    return service


def make_app(service):
    app = MediaTestApp()
    app._media_service = service
    return app


def footer_key(screen, key):
    footer = screen.query_one("#media-footer", Footer)
    return next(
        widget
        for widget in footer.query("FooterKey")
        if getattr(widget, "key", None) == key
    )


def bookmark(url=URL):
    return Entry(
        RaindropItem.model_validate(
            {
                "_id": 1,
                "title": "Example",
                "excerpt": "Description",
                "link": url,
                "created": "2026-01-01T00:00:00Z",
                "lastUpdate": "2026-01-01T00:00:00Z",
                "collection": {"_id": 0},
                "type": "video",
                "user": {},
            }
        )
    )


@pytest.mark.parametrize("size", [(80, 24), (140, 80)])
def test_media_panel_matches_markdown_preview(service, size):
    app = make_app(service)

    async def run():
        async with app.run_test(size=size) as pilot:
            app.push_screen(MarkdownModalScreen("# Article preview"))
            await pilot.pause()
            viewer = app.screen.query_one(MarkdownViewer)
            expected_region = viewer.region
            expected_styles = {
                key: getattr(viewer.styles, key)
                for key in (
                    "padding",
                    "border",
                    "background",
                    "max_width",
                    "max_height",
                )
            }
            await pilot.press("space")
            app.preview_media(URL)
            await pilot.pause()
            panel = app.screen.query_one("#media-panel")
            assert panel.region == expected_region
            for key, expected in expected_styles.items():
                assert getattr(panel.styles, key) == expected

    asyncio.run(run())


def test_media_footer_actions_and_click_to_close(service):
    app = make_app(service)

    async def run():
        async with app.run_test(size=(120, 45)) as pilot:
            app.preview_media(URL)
            await pilot.pause()
            footer = app.screen.query_one("#media-footer", Footer)
            actions = {
                getattr(widget, "key", None): getattr(
                    widget, "description", None
                )
                for widget in footer.query("FooterKey")
            }
            assert actions == {
                "ctrl+s": "Download",
                "r": "Refresh",
                "x": "Cancel job",
                "space": "Close",
            }
            assert not app.screen.query(Button)
            await pilot.click(footer_key(app.screen, "space"))
            assert not isinstance(app.screen, MediaModalScreen)

    asyncio.run(run())


def test_download_footer_disabled_until_metadata_is_ready(service, monkeypatch):
    info = service.cached(URL)
    release = asyncio.Event()

    async def discover(*args, **kwargs):
        await release.wait()
        return info

    monkeypatch.setattr(service, "cached", lambda _: None)
    monkeypatch.setattr(service, "discover", discover)
    app = make_app(service)

    async def run():
        async with app.run_test(size=(120, 45)) as pilot:
            app.preview_media(URL)
            await pilot.pause()
            assert footer_key(app.screen, "ctrl+s").has_class("-disabled")
            await pilot.press("ctrl+s")
            await pilot.click(footer_key(app.screen, "ctrl+s"))
            assert not app._media_downloads
            release.set()
            await pilot.pause()
            assert not footer_key(app.screen, "ctrl+s").has_class("-disabled")

    asyncio.run(run())


def test_cached_picker_selection_and_subtitle_enter(service, monkeypatch):
    discover = AsyncMock()
    monkeypatch.setattr(service, "discover", discover)
    app = make_app(service)

    async def run():
        async with app.run_test(size=(120, 45)) as pilot:
            app.preview_media(URL)
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, MediaModalScreen)
            assert screen.info is not None
            assert screen.query_one("#media-video", Select).value == "f:v"
            assert "Cached" in str(
                screen.query_one("#media-cache", Static).render()
            )
            subtitles = screen.query_one("#media-subtitles", SelectionList)
            subtitles.focus()
            await pilot.press("enter")
            assert subtitles.selected == ["manual:en:vtt"]
            assert isinstance(app.screen, MediaModalScreen)
            await pilot.press("space")
            assert not isinstance(app.screen, MediaModalScreen)

    asyncio.run(run())
    discover.assert_not_called()


@pytest.mark.parametrize(
    "control",
    [
        "#media-video",
        "#media-audio",
        "#media-subtitles",
        "#media-form",
    ],
)
def test_space_closes_from_any_control(service, control):
    app = make_app(service)

    async def run():
        async with app.run_test(size=(120, 45)) as pilot:
            app.preview_media(URL)
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, MediaModalScreen)
            screen.query_one(control).focus()
            await pilot.press("space")
            assert not isinstance(app.screen, MediaModalScreen)
            assert not app._media_downloads

    asyncio.run(run())


def test_space_closes_expanded_format_selector(service):
    app = make_app(service)

    async def run():
        async with app.run_test(size=(120, 45)) as pilot:
            app.preview_media(URL)
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, MediaModalScreen)
            video = screen.query_one("#media-video", Select)
            video.focus()
            await pilot.press("enter")
            assert video.expanded
            await pilot.press("space")
            assert not isinstance(app.screen, MediaModalScreen)

    asyncio.run(run())


def test_stale_cache_immediate_display_refresh_preserves_choices(
    service, monkeypatch
):
    info = service.cached(URL)
    assert info is not None
    info.fetched_at = time.time() - 30000
    started = asyncio.Event()
    release = asyncio.Event()

    async def discover(*args, **kwargs):
        started.set()
        await release.wait()
        return info.model_copy(update={"title": "Refreshed"})

    monkeypatch.setattr(service, "discover", discover)
    app = make_app(service)

    async def run():
        async with app.run_test(size=(120, 45)) as pilot:
            app.preview_media(URL)
            await started.wait()
            screen = app.screen
            assert isinstance(screen, MediaModalScreen)
            assert screen.info is not None
            screen.query_one("#media-video", Select).value = "none"
            screen.query_one("#media-audio", Select).value = "f:a"
            release.set()
            await pilot.pause()
            assert screen.info.title == "Refreshed"
            assert screen.query_one("#media-video", Select).value == "none"
            assert screen.query_one("#media-audio", Select).value == "f:a"

    asyncio.run(run())


def test_refresh_failure_keeps_cached_choices(service, monkeypatch):
    monkeypatch.setattr(
        service, "discover", AsyncMock(side_effect=ValueError("geo blocked"))
    )
    app = make_app(service)

    async def run():
        async with app.run_test(size=(120, 45)) as pilot:
            app.preview_media(URL)
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, MediaModalScreen)
            await pilot.press("r")
            await pilot.pause()
            assert "geo blocked" in str(
                screen.query_one("#media-cache", Static).render()
            )
            assert screen.info is not None
            assert screen.check_action("download", ()) is True

    asyncio.run(run())


def test_download_survives_close_and_can_be_cancelled_on_reopen(
    service, monkeypatch
):
    started = threading.Event()

    def download(url, selection, cancel, progress):
        started.set()
        progress("Downloading 10%")
        assert cancel.wait(5)
        raise DownloadCancelled()

    monkeypatch.setattr(service, "download", download)
    app = make_app(service)

    async def run():
        async with app.run_test(size=(120, 45)) as pilot:
            app.preview_media(URL)
            await pilot.pause()
            assert not app.screen.query(Button)
            assert not footer_key(app.screen, "ctrl+s").has_class("-disabled")
            assert footer_key(app.screen, "x").has_class("-disabled")
            await pilot.click(footer_key(app.screen, "ctrl+s"))
            assert await asyncio.to_thread(started.wait, 2)
            job = app._media_downloads[0]
            await pilot.press("space")
            assert not job.cancel.is_set()
            assert not job.done
            app.preview_media(URL)
            await pilot.pause()
            assert footer_key(app.screen, "ctrl+s").has_class("-disabled")
            assert not footer_key(app.screen, "x").has_class("-disabled")
            await pilot.click(footer_key(app.screen, "x"))
            await pilot.pause()
            assert job.cancel.is_set()
            assert job.done
            assert job.status == "Download cancelled"
            await pilot.pause(0.3)
            assert not footer_key(app.screen, "ctrl+s").has_class("-disabled")
            assert footer_key(app.screen, "x").has_class("-disabled")

    asyncio.run(run())


def test_selection_error_is_not_hidden_by_completed_job(service):
    app = make_app(service)
    app._media_downloads.append(
        MediaDownload(
            URL, DownloadSelection(video="v"), status="Saved", done=True
        )
    )

    async def run():
        async with app.run_test(size=(120, 45)) as pilot:
            app.preview_media(URL)
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, MediaModalScreen)
            screen.query_one("#media-video", Select).value = "none"
            screen.query_one("#media-audio", Select).value = "none"
            screen.action_download()
            await pilot.pause(0.3)
            assert "Select video, audio or subtitles" in str(
                screen.query_one("#media-progress", Static).render()
            )
            assert len(app._media_downloads) == 1

    asyncio.run(run())


def test_job_history_keeps_active_jobs_in_order(service, monkeypatch):
    monkeypatch.setattr(
        service, "download", lambda *args: service.config.download_dir
    )
    app = make_app(service)
    selection = DownloadSelection(video="v")
    old = MediaDownload(URL, selection, done=True)
    app._media_downloads.append(old)

    async def run():
        async with app.run_test(size=(120, 45)):
            current = app.start_media_download(URL, selection)
            app.start_media_download("https://example.org/other", selection)
            assert app.start_media_download(URL, selection) is current
            assert app._media_downloads.index(old) < app._media_downloads.index(
                current
            )
            await app.workers.wait_for_complete()
            assert current.done
            assert current.status.startswith("Saved to ")

    asyncio.run(run())


def test_space_routes_media_without_article_network_request(
    service, monkeypatch
):
    instance = MagicMock(
        side_effect=AssertionError("article lookup must not run")
    )
    monkeypatch.setattr("kiosque.tui.raindrop.Website.instance", instance)
    app = make_app(service)

    async def run():
        async with app.run_test(size=(120, 45)) as pilot:
            entry = bookmark()
            await app.query_one(VerticalScroll).mount(entry)
            entry.focus()
            await pilot.press("space")
            await pilot.pause()
            assert isinstance(app.screen, MediaModalScreen)
            await pilot.press("space")
            assert not isinstance(app.screen, MediaModalScreen)
            assert entry.has_focus

    asyncio.run(run())
    instance.assert_not_called()


def test_unsupported_preview_does_not_open_media_picker(service, monkeypatch):
    monkeypatch.setattr(
        "kiosque.tui.raindrop.Website.instance",
        MagicMock(side_effect=ValueError("Unsupported URL")),
    )
    discover = AsyncMock(side_effect=ValueError("No embedded media"))
    monkeypatch.setattr(service, "discover", discover)
    app = make_app(service)
    notify = MagicMock()
    monkeypatch.setattr(app, "notify", notify)

    async def run():
        async with app.run_test(size=(120, 45)) as pilot:
            entry = bookmark("https://example.org/article")
            await app.query_one(VerticalScroll).mount(entry)
            entry.focus()
            await pilot.press("space")
            await pilot.pause()
            assert not isinstance(app.screen, MediaModalScreen)
            assert entry.has_focus
            discover.assert_not_called()
            assert notify.call_args is not None
            assert notify.call_args.args == ("No preview available",)
            assert notify.call_args.kwargs["severity"] == "warning"
            await pilot.press("m")
            await pilot.pause()
            assert isinstance(app.screen, MediaModalScreen)
            discover.assert_awaited_once()

    asyncio.run(run())


def test_article_preview_preserved_and_explicit_media_action(
    service, monkeypatch
):
    website = MagicMock()
    website.full_text.return_value = "# An article"
    monkeypatch.setattr(
        "kiosque.tui.raindrop.Website.instance", lambda _: website
    )
    app = make_app(service)

    async def run():
        async with app.run_test(size=(120, 45)) as pilot:
            entry = bookmark("https://example.org/article")
            await app.query_one(VerticalScroll).mount(entry)
            entry.focus()
            await pilot.press("space")
            await pilot.pause()
            assert isinstance(app.screen, MarkdownModalScreen)
            await pilot.press("space")
            entry.url = URL
            entry.focus()
            await pilot.press("m")
            await pilot.pause()
            assert isinstance(app.screen, MediaModalScreen)

    asyncio.run(run())
