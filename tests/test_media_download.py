"""Exercise yt-dlp itself against local HTTP fixtures, never public media."""

import asyncio
import functools
import io
import json
import shutil
import subprocess
import threading
import wave
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pytest

from kiosque.core.config import MediaConfig
from kiosque.core.media import DownloadSelection, MediaService


@pytest.fixture
def local_media(tmp_path):
    audio = io.BytesIO()
    with wave.open(audio, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(8000)
        stream.writeframes(b"\x00\x00" * 800)
    (tmp_path / "sample.wav").write_bytes(audio.getvalue())
    (tmp_path / "captions.vtt").write_text(
        "WEBVTT\n\n00:00.000 --> 00:00.100\nHello\n"
    )
    (tmp_path / "captions.srt").write_text(
        "1\n00:00:00,000 --> 00:00:00,100\nHello\n"
    )

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(Handler, directory=tmp_path)
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", audio.getvalue()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


@pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
    reason="Optional external ffmpeg tools are not installed",
)
def test_real_library_merges_video_and_audio(
    local_media, tmp_path, monkeypatch
):
    base, _ = local_media
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=size=16x16:rate=1",
            "-t",
            "1",
            "-c:v",
            "mpeg4",
            str(tmp_path / "video.mp4"),
        ],
        check=True,
        timeout=15,
    )
    service = MediaService(
        MediaConfig(download_dir=tmp_path / "output"),
        cache_dir=tmp_path / "cache",
    )
    raw = {
        "id": "merge",
        "title": "Merge",
        "extractor": "generic",
        "webpage_url": f"{base}/video.mp4",
        "extractor_key": "Generic",
        "formats": [
            {
                "format_id": "a",
                "url": f"{base}/sample.wav",
                "ext": "wav",
                "vcodec": "none",
                "acodec": "pcm_s16le",
            },
            {
                "format_id": "v",
                "url": f"{base}/video.mp4",
                "ext": "mp4",
                "vcodec": "mp4v",
                "acodec": "none",
            },
        ],
    }
    monkeypatch.setattr(service, "_extract", lambda _: raw)
    destination = service.download(
        f"{base}/video.mp4",
        DownloadSelection(video="v"),
        threading.Event(),
        lambda _: None,
    )
    output = list(destination.glob("*.mkv"))
    assert len(output) == 1
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-of",
            "json",
            str(output[0]),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    streams = json.loads(probe.stdout)["streams"]
    assert {stream["codec_type"] for stream in streams} == {"video", "audio"}


def test_real_library_generic_discovery_and_download(local_media, tmp_path):
    base, expected = local_media
    service = MediaService(
        MediaConfig(download_dir=tmp_path / "output"),
        cache_dir=tmp_path / "cache",
    )
    url = f"{base}/sample.wav"
    info = asyncio.run(service.discover(url))
    assert len(info.formats) == 1
    assert info.formats[0].has_audio
    assert not info.formats[0].has_video
    destination = service.download(
        url,
        DownloadSelection(audio=info.formats[0].id),
        threading.Event(),
        lambda _: None,
    )
    output = list(destination.glob("*.wav"))
    assert len(output) == 1
    assert output[0].read_bytes() == expected


@pytest.mark.parametrize("with_media", [True, False])
def test_real_library_downloads_all_selected_subtitle_variants(
    local_media, tmp_path, monkeypatch, with_media
):
    base, _ = local_media
    service = MediaService(
        MediaConfig(download_dir=tmp_path / "output"),
        cache_dir=tmp_path / "cache",
    )
    raw = {
        "id": "example",
        "title": "Local captions",
        "extractor": "generic",
        "webpage_url": f"{base}/sample.wav",
        "extractor_key": "Generic",
        "formats": [
            {
                "format_id": "audio",
                "url": f"{base}/sample.wav",
                "ext": "wav",
                "vcodec": "none",
                "acodec": "pcm_s16le",
            }
        ],
        "subtitles": {
            "en": [
                {"ext": "vtt", "url": f"{base}/captions.vtt"},
                {"ext": "srt", "url": f"{base}/captions.srt"},
            ]
        },
        "automatic_captions": {
            "en": [{"ext": "vtt", "url": f"{base}/captions.vtt"}]
        },
    }
    if not with_media:
        raw["formats"] = []
    monkeypatch.setattr(service, "_extract", lambda _: raw)
    destination = service.download(
        f"{base}/sample.wav",
        DownloadSelection(
            audio=None,
            subtitles=["manual:en:vtt", "manual:en:srt", "auto:en:vtt"],
        ),
        threading.Event(),
        lambda _: None,
    )
    assert len(list(destination.glob("*.vtt"))) == 2
    assert len(list(destination.glob("*.srt"))) == 1
    assert not list(destination.glob("*.wav"))
    assert all("Hello" in path.read_text() for path in destination.iterdir())
