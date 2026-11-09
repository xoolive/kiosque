"""Media discovery/selection tests: no network or actual media downloads."""

import asyncio
import json
import threading
import time
from unittest.mock import MagicMock

import pytest

from kiosque.core.config import MediaConfig
from kiosque.core.media import (
    DownloadCancelled,
    DownloadSelection,
    MediaError,
    MediaService,
    has_media_extractor,
    normalize_info,
)

URL = "https://www.youtube.com/watch?v=example"


@pytest.fixture
def raw():
    return {
        "id": "example",
        "title": "Example",
        "extractor": "youtube",
        "formats": [
            {
                "format_id": "storyboard",
                "ext": "mhtml",
                "url": "secret",
                "vcodec": "none",
                "acodec": "none",
            },
            {
                "format_id": "drm",
                "ext": "mp4",
                "url": "secret",
                "has_drm": True,
            },
            {
                "format_id": "audio-en",
                "ext": "m4a",
                "url": "secret",
                "vcodec": "none",
                "acodec": "aac",
                "language": "en",
            },
            {
                "format_id": "audio-fr",
                "ext": "m4a",
                "url": "secret",
                "vcodec": "none",
                "acodec": "aac",
                "language": "fr",
            },
            {
                "format_id": "720",
                "ext": "mp4",
                "url": "secret",
                "vcodec": "h264",
                "acodec": "none",
                "language": "en",
            },
            {
                "format_id": "combined",
                "ext": "mp4",
                "url": "secret",
                "vcodec": "h264",
                "acodec": "aac",
                "format_note": "Original [VO]",
            },
        ],
        "subtitles": {
            "en": [
                {"ext": "vtt", "url": "secret"},
                {"ext": "srt", "url": "secret"},
            ]
        },
        "automatic_captions": {"en": [{"ext": "vtt", "url": "secret"}]},
        "http_headers": {"Cookie": "secret"},
    }


@pytest.fixture
def service(tmp_path):
    return MediaService(
        MediaConfig(download_dir=tmp_path / "downloads"),
        cache_dir=tmp_path / "cache",
    )


def test_normalize_excludes_non_media_and_credentials(raw):
    info = normalize_info(raw)
    assert [fmt.id for fmt in info.formats] == [
        "audio-en",
        "audio-fr",
        "720",
        "combined",
    ]
    assert len(info.subtitles) == 3
    assert "Original [VO]" in info.formats[-1].label
    assert "secret" not in info.model_dump_json()
    assert "http_headers" not in info.model_dump_json()


@pytest.mark.parametrize(
    "extra",
    [
        {"_type": "playlist", "entries": []},
        {"is_live": True},
        {"live_status": "is_upcoming"},
    ],
)
def test_reject_unbounded_downloads(raw, extra):
    raw.update(extra)
    with pytest.raises(MediaError):
        normalize_info(raw)


def test_persistent_cache_hit(service, raw, monkeypatch):
    extract = MagicMock(return_value=raw)
    monkeypatch.setattr(service, "_extract", extract)
    first = asyncio.run(service.discover(URL))
    second = asyncio.run(service.discover(URL))
    assert first == second
    extract.assert_called_once()
    other = MediaService(service.config, cache_dir=service.cache_dir)
    assert other.cached(URL) == first
    assert "secret" not in next(service.cache_dir.glob("*.json")).read_text()


def test_stale_cache_force_and_corruption(service, raw, monkeypatch):
    extract = MagicMock(return_value=raw)
    monkeypatch.setattr(service, "_extract", extract)
    info = asyncio.run(service.discover(URL))
    info.fetched_at = time.time() - service.config.cache_ttl - 1
    assert not service.is_fresh(info)
    asyncio.run(service.discover(URL))
    asyncio.run(service.discover(URL, force=True))
    assert extract.call_count == 3
    service._memory.clear()
    next(service.cache_dir.glob("*.json")).write_text("invalid json")
    assert service.cached(URL) is None


def test_cache_context_and_read_only_failure(service, raw, monkeypatch):
    service._store(URL, normalize_info(raw))
    other = MediaService(
        service.config, proxy="socks5://different", cache_dir=service.cache_dir
    )
    assert other.cached(URL) is None
    service.cache_dir = service.cache_dir / "not-a-directory"
    service.cache_dir.write_text("file")
    monkeypatch.setattr(service, "_extract", lambda _: raw)
    assert asyncio.run(service.discover(URL, force=True)).title == "Example"


def test_concurrent_discovery_single_flight(service, raw, monkeypatch):
    started = threading.Event()
    release = threading.Event()

    def extract(_):
        started.set()
        assert release.wait(5)
        return raw

    mock = MagicMock(side_effect=extract)
    monkeypatch.setattr(service, "_extract", mock)

    async def run():
        first = asyncio.create_task(service.discover(URL))
        assert await asyncio.to_thread(started.wait, 5)
        second = asyncio.create_task(service.discover(URL))
        await asyncio.sleep(0.02)
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
        release.set()
        assert (await second).title == "Example"

    asyncio.run(run())
    mock.assert_called_once()


def test_video_audio_pairing(service, raw, monkeypatch):
    monkeypatch.setattr(
        "kiosque.core.media.shutil.which", lambda _: "/bin/ffmpeg"
    )
    options = service.download_options(
        normalize_info(raw), DownloadSelection(video="720")
    )
    assert options["format"] == "720+audio-en"
    assert options["merge_output_format"] == "mkv"
    assert not options["skip_download"]


def test_auto_audio_does_not_change_known_language(service, raw, monkeypatch):
    monkeypatch.setattr(
        "kiosque.core.media.shutil.which", lambda _: "/bin/ffmpeg"
    )
    info = normalize_info(raw)
    next(fmt for fmt in info.formats if fmt.id == "720").language = "de"
    with pytest.raises(MediaError, match="No matching audio"):
        service.download_options(info, DownloadSelection(video="720"))


def test_cache_is_bounded(service, raw, monkeypatch):
    monkeypatch.setattr("kiosque.core.media.CACHE_LIMIT", 2)
    info = normalize_info(raw)
    for index in range(5):
        service._store(f"https://example.org/{index}", info)
    assert len(service._memory) == 2
    assert len(list(service.cache_dir.glob("*.json"))) == 2


def test_missing_ffmpeg(service, raw, monkeypatch):
    monkeypatch.setattr("kiosque.core.media.shutil.which", lambda _: None)
    with pytest.raises(MediaError, match="ffmpeg"):
        service.download_options(
            normalize_info(raw), DownloadSelection(video="720")
        )


@pytest.mark.parametrize(
    "selection",
    [
        DownloadSelection(video="gone"),
        DownloadSelection(video="720", audio="gone"),
        DownloadSelection(video="combined", audio="audio-en"),
        DownloadSelection(video="combined", audio=None),
        DownloadSelection(video=None, audio=None),
        DownloadSelection(video=None, audio=None, subtitles=["gone"]),
    ],
)
def test_invalid_selections(service, raw, selection):
    with pytest.raises(MediaError):
        service.download_options(normalize_info(raw), selection)


def test_subtitle_only_and_audio_only(service, raw):
    info = normalize_info(raw)
    options = service.download_options(
        info, DownloadSelection(audio=None, subtitles=["manual:en:vtt"])
    )
    assert options["skip_download"]
    options = service.download_options(
        info, DownloadSelection(audio="audio-en")
    )
    assert options["format"] == "audio-en"
    assert "postprocessors" not in options
    with_subtitles = service.download_options(
        info, DownloadSelection(audio="audio-en", subtitles=["manual:en:vtt"])
    )
    assert options["outtmpl"] == with_subtitles["outtmpl"]


def test_arte_combined_audio_extraction(service, raw, monkeypatch):
    monkeypatch.setattr(
        "kiosque.core.media.shutil.which", lambda _: "/bin/ffmpeg"
    )
    raw["formats"] = raw["formats"][-1:]
    options = service.download_options(normalize_info(raw), DownloadSelection())
    assert options["format"] == "combined"
    assert options["postprocessors"][0]["key"] == "FFmpegExtractAudio"
    explicit = service.download_options(
        normalize_info(raw), DownloadSelection(audio="combined")
    )
    assert explicit["format"] == "combined"
    assert explicit["postprocessors"][0]["key"] == "FFmpegExtractAudio"


def test_download_refreshes_and_preserves_all_subtitle_variants(
    service, raw, monkeypatch
):
    monkeypatch.setattr(service, "_extract", lambda _: raw)
    calls = []

    class Downloader:
        def __init__(self, options):
            calls.append(options)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def process_ie_result(self, info, download):
            assert info["formats"][-1]["url"] == "secret"
            assert download

    monkeypatch.setattr("kiosque.core.media.YoutubeDL", Downloader)
    selection = DownloadSelection(
        video="combined",
        subtitles=["manual:en:vtt", "manual:en:srt", "auto:en:vtt"],
    )
    destination = service.download(
        URL, selection, threading.Event(), lambda _: None
    )
    assert destination == service.config.download_dir
    assert len(calls) == 4
    assert [call.get("subtitlesformat") for call in calls] == [
        None,
        "vtt",
        "srt",
        "vtt",
    ]
    assert calls[-1]["writeautomaticsub"]
    assert not calls[-1]["writesubtitles"]
    assert len({call["outtmpl"] for call in calls}) == 4


def test_cancel_download_before_extraction(service, monkeypatch):
    extract = MagicMock()
    monkeypatch.setattr(service, "_extract", extract)
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(DownloadCancelled):
        service.download(URL, DownloadSelection(), cancel, lambda _: None)
    extract.assert_not_called()


def test_cache_schema_and_version_isolation(service, raw, monkeypatch):
    service._store(URL, normalize_info(raw))
    monkeypatch.setattr("kiosque.core.media.ytdlp_version", "different")
    assert service.cached(URL) is None
    assert (
        json.loads(next(service.cache_dir.glob("*.json")).read_text())["title"]
        == "Example"
    )


def test_extractor_routing():
    assert has_media_extractor("https://www.youtube.com/watch?v=YE7VzlLtp-4")
    assert has_media_extractor(
        "https://www.arte.tv/fr/videos/109067-000-A/example/"
    )
    assert not has_media_extractor("https://example.org/article")
    assert not has_media_extractor("file:///tmp/movie.mp4")
