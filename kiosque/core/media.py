"""yt-dlp library integration and a credential-free format-list cache."""

from __future__ import annotations

import asyncio
import copy
import hashlib
import logging
import os
import re
import shutil
import tempfile
import threading
import time
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from appdirs import user_cache_dir
from pydantic import BaseModel, Field, ValidationError
from yt_dlp import YoutubeDL
from yt_dlp.extractor import gen_extractor_classes
from yt_dlp.version import __version__ as ytdlp_version

from kiosque.core.config import MediaConfig

logger = logging.getLogger(__name__)
CACHE_SCHEMA = 1
CACHE_LIMIT = 128


class MediaError(Exception):
    """A discovery or selection failure suitable for display to the user."""


class DownloadCancelled(MediaError):
    """A cooperatively cancelled download."""


class MediaFormat(BaseModel):
    id: str
    ext: str
    resolution: str = ""
    vcodec: str = "none"
    acodec: str = "none"
    language: str = ""
    note: str = ""
    fps: float | None = None
    bitrate: float | None = None
    size: int | None = None
    approximate_size: bool = False

    @property
    def has_video(self) -> bool:
        return self.vcodec != "none"

    @property
    def has_audio(self) -> bool:
        return self.acodec != "none"

    @property
    def label(self) -> str:
        parts = [self.id, self.ext, self.resolution, self.language, self.note]
        if self.fps:
            parts.append(f"{self.fps:g}fps")
        parts.append(f"{self.vcodec}/{self.acodec}")
        if self.bitrate:
            parts.append(f"{self.bitrate:g}kbit/s")
        if self.size:
            prefix = "~" if self.approximate_size else ""
            parts.append(f"{prefix}{self.size / 1024**2:.1f}MiB")
        return " · ".join(part for part in parts if part)


class SubtitleTrack(BaseModel):
    language: str
    ext: str
    automatic: bool = False
    name: str = ""

    @property
    def key(self) -> str:
        source = "auto" if self.automatic else "manual"
        return f"{source}:{self.language}:{self.ext}"

    @property
    def label(self) -> str:
        kind = "automatic" if self.automatic else "subtitles"
        return f"{self.language} · {self.ext} · {kind} {self.name}".strip()


class MediaInfo(BaseModel):
    """Only display metadata: no stream URLs, cookies or HTTP headers."""

    id: str
    title: str
    formats: list[MediaFormat]
    subtitles: list[SubtitleTrack]
    fetched_at: float = Field(default_factory=time.time, allow_inf_nan=False)


class DownloadSelection(BaseModel):
    video: str | None = None
    audio: str | None = "auto"
    subtitles: list[str] = Field(default_factory=list)


class _QuietLogger:
    """Never let yt-dlp write terminal output over Textual."""

    def debug(self, message: str) -> None:
        pass

    def warning(self, message: str) -> None:
        logger.debug("yt-dlp: %s", message)

    def error(self, message: str) -> None:
        logger.debug("yt-dlp: %s", message)


@lru_cache(maxsize=1)
def _extractors() -> tuple[Any, ...]:
    return tuple(gen_extractor_classes())


def has_media_extractor(url: str) -> bool:
    """A cheap routing hint, never a guarantee of availability."""
    if urlsplit(url).scheme not in {"http", "https"}:
        return False
    return any(
        ie.IE_NAME != "generic" and ie.suitable(url) for ie in _extractors()
    )


def normalize_info(raw: dict[str, Any]) -> MediaInfo:
    """Reduce a yt-dlp result to a safely persistable format catalogue."""
    if raw.get("_type") in {"playlist", "multi_video"} or "entries" in raw:
        raise MediaError("Choose a single video, not a playlist or channel.")
    if raw.get("is_live") or raw.get("live_status") in {
        "is_live",
        "is_upcoming",
        "post_live",
    }:
        raise MediaError("Live and upcoming streams are not supported yet.")
    formats = []
    for fmt in raw.get("formats", []):
        if fmt.get("has_drm") or not fmt.get("url"):
            continue
        video = fmt.get("vcodec") or "unknown"
        audio = fmt.get("acodec") or "unknown"
        if video == audio == "none" or fmt.get("ext") in {
            "mhtml",
            "jpg",
            "png",
        }:
            continue
        formats.append(
            MediaFormat(
                id=str(fmt["format_id"]),
                ext=fmt.get("ext") or "unknown",
                resolution=fmt.get("resolution") or "",
                vcodec=video,
                acodec=audio,
                language=fmt.get("language") or "",
                note=fmt.get("format_note") or "",
                fps=fmt.get("fps"),
                bitrate=fmt.get("tbr") or fmt.get("abr"),
                size=fmt.get("filesize") or fmt.get("filesize_approx"),
                approximate_size=not bool(fmt.get("filesize")),
            )
        )
    subtitles: list[SubtitleTrack] = []
    seen: set[str] = set()
    for source, automatic in (
        ("subtitles", False),
        ("automatic_captions", True),
    ):
        for language, variants in (raw.get(source) or {}).items():
            if language == "live_chat":
                continue
            for variant in variants:
                if not variant.get("ext"):
                    continue
                track = SubtitleTrack(
                    language=language,
                    ext=variant["ext"],
                    automatic=automatic,
                    name=variant.get("name") or "",
                )
                if track.key not in seen:
                    seen.add(track.key)
                    subtitles.append(track)
    if not formats and not subtitles:
        raise MediaError(
            "No downloadable media or subtitles found (possibly DRM)."
        )
    return MediaInfo(
        id=str(raw.get("id", "")),
        title=raw.get("title") or "Untitled",
        formats=formats,
        subtitles=subtitles,
    )


class MediaService:
    """Async discovery with single-flight requests and bounded disk caching.

    Extraction and downloading use the Python library in worker threads. Cached
    catalogue data never includes the signed URLs required to download media.
    """

    def __init__(
        self,
        config: MediaConfig,
        *,
        proxy: str | None = None,
        cache_dir: Path | None = None,
    ) -> None:
        self.config = config
        self.proxy = proxy
        self.cache_dir = cache_dir or Path(user_cache_dir("kiosque")) / "media"
        self._memory: dict[str, MediaInfo] = {}
        self._pending: dict[str, asyncio.Task[MediaInfo]] = {}
        self._lock = threading.RLock()

    def _key(self, url: str) -> str:
        # The digest scopes the cache to the effective network context without
        # persisting proxy credentials or the source URL (which may be signed).
        context = f"{CACHE_SCHEMA}\0{ytdlp_version}\0{self.proxy}\0{url}"
        return hashlib.sha256(context.encode()).hexdigest()

    def is_fresh(self, info: MediaInfo) -> bool:
        return 0 <= time.time() - info.fetched_at < self.config.cache_ttl

    def cached(self, url: str) -> MediaInfo | None:
        key = self._key(url)
        with self._lock:
            if key in self._memory:
                return self._memory[key]
            try:
                info = MediaInfo.model_validate_json(
                    (self.cache_dir / f"{key}.json").read_text()
                )
            except (OSError, ValueError, ValidationError):
                return None
            self._remember(key, info)
            return info

    def _remember(self, key: str, info: MediaInfo) -> None:
        self._memory[key] = info
        while len(self._memory) > CACHE_LIMIT:
            del self._memory[next(iter(self._memory))]

    def _store(self, url: str, info: MediaInfo) -> None:
        with self._lock:
            key = self._key(url)
            self._remember(key, info)
            temporary: str | None = None
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
                with tempfile.NamedTemporaryFile(
                    mode="w", dir=self.cache_dir, delete=False
                ) as stream:
                    temporary = stream.name
                    stream.write(info.model_dump_json())
                os.replace(temporary, self.cache_dir / f"{key}.json")
                files = sorted(
                    self.cache_dir.glob("*.json"),
                    key=lambda path: path.stat().st_mtime,
                    reverse=True,
                )
                for path in files[CACHE_LIMIT:]:
                    path.unlink(missing_ok=True)
            except OSError:
                logger.debug("Cannot persist media cache", exc_info=True)
            finally:
                if temporary:
                    Path(temporary).unlink(missing_ok=True)

    def _options(self) -> dict[str, Any]:
        options: dict[str, Any] = {
            "quiet": True,
            "noprogress": True,
            "logger": _QuietLogger(),
            "noplaylist": True,
            "extract_flat": "in_playlist",
            "playlistend": 1,
            "socket_timeout": 20,
            "retries": 1,
            "allow_playlist_files": False,
            "ignore_no_formats_error": True,
        }
        if self.proxy:
            options["proxy"] = self.proxy
        return options

    def _extract(self, url: str) -> dict[str, Any]:
        if urlsplit(url).scheme not in {"http", "https"}:
            raise MediaError("Only HTTP(S) media URLs are supported.")
        with YoutubeDL(self._options()) as ydl:
            raw = ydl.extract_info(url, download=False)
        if raw is None:
            raise MediaError("No media information returned.")
        return raw

    def _discover(self, url: str) -> MediaInfo:
        info = normalize_info(self._extract(url))
        self._store(url, info)
        return info

    async def discover(self, url: str, *, force: bool = False) -> MediaInfo:
        if not force:
            cached = await asyncio.to_thread(self.cached, url)
            if cached is not None and self.is_fresh(cached):
                return cached
        key = self._key(url)
        if key not in self._pending:
            task = asyncio.create_task(asyncio.to_thread(self._discover, url))
            self._pending[key] = task

            def done(finished: asyncio.Task[MediaInfo]) -> None:
                self._pending.pop(key, None)
                # Retrieve an exception even when every UI waiter has closed.
                if not finished.cancelled():
                    finished.exception()

            task.add_done_callback(done)
        return await asyncio.shield(self._pending[key])

    def download(
        self,
        url: str,
        selection: DownloadSelection,
        cancel: threading.Event,
        progress: Callable[[str], None],
    ) -> Path:
        """Refresh signed URLs, validate exact selections, then download.

        Cancellation is checked at extraction boundaries and download/PP hooks;
        an ffmpeg operation already running may finish before the next hook.
        """

        def check_cancel() -> None:
            if cancel.is_set():
                raise DownloadCancelled("Download cancelled")

        def hook(data: dict[str, Any]) -> None:
            check_cancel()
            status = data.get("status", "")
            if status == "downloading":
                total = data.get("total_bytes") or data.get(
                    "total_bytes_estimate"
                )
                downloaded = data.get("downloaded_bytes", 0)
                percent = (
                    f"{downloaded / total:.0%}"
                    if total
                    else f"{downloaded / 1024**2:.1f}MiB"
                )
                progress(f"Downloading {percent}")
            elif status == "finished":
                progress("Processing downloaded files…")
            else:
                progress("Merging / processing…")

        check_cancel()
        progress("Refreshing download URLs…")
        raw = self._extract(url)
        check_cancel()
        info = normalize_info(raw)
        self._store(url, info)
        options = self.download_options(info, selection)
        destination = self.config.download_dir.expanduser().resolve()
        destination.mkdir(parents=True, exist_ok=True)
        options.update(self._options())
        options.update(
            {
                "paths": {"home": str(destination)},
                "progress_hooks": [hook],
                "postprocessor_hooks": [hook],
                "overwrites": False,
            }
        )
        # Use fresh raw metadata rather than extracting a second time. It stays
        # in memory and is never written into the display cache.
        try:
            if not options["skip_download"]:
                with YoutubeDL(options) as ydl:
                    ydl.process_ie_result(copy.deepcopy(raw), download=True)
            tracks = {track.key: track for track in info.subtitles}
            for key in selection.subtitles:
                check_cancel()
                track = tracks[key]
                progress(f"Downloading {track.label}…")
                subtitle_options = dict(options)
                track_id = hashlib.sha256(key.encode()).hexdigest()[:10]
                subtitle_options.update(
                    {
                        "skip_download": True,
                        "writesubtitles": not track.automatic,
                        "writeautomaticsub": track.automatic,
                        "subtitleslangs": [re.escape(track.language)],
                        "subtitlesformat": track.ext,
                        "outtmpl": options["outtmpl"].replace(
                            "].%(ext)s", f"] [sub-{track_id}].%(ext)s"
                        ),
                        "postprocessors": [],
                    }
                )
                with YoutubeDL(subtitle_options) as ydl:
                    ydl.process_ie_result(copy.deepcopy(raw), download=True)
            check_cancel()
        except Exception as exc:
            if cancel.is_set():
                raise DownloadCancelled("Download cancelled") from exc
            raise
        return destination

    def download_options(
        self, info: MediaInfo, selection: DownloadSelection
    ) -> dict[str, Any]:
        """Build explicit format/subtitle options; never substitute versions."""
        by_id = {fmt.id: fmt for fmt in info.formats}
        video = by_id.get(selection.video) if selection.video else None
        if selection.video and (video is None or not video.has_video):
            raise MediaError(
                "Selected video is no longer available; refresh the list."
            )
        audio = (
            by_id.get(selection.audio) if selection.audio != "auto" else None
        )
        if selection.audio not in {None, "auto"} and (
            audio is None
            or not audio.has_audio
            or (audio.has_video and video is not None)
        ):
            raise MediaError(
                "Selected audio is no longer available; refresh the list."
            )
        options: dict[str, Any] = {}
        formats: list[str] = []
        needs_ffmpeg = False
        if video:
            formats.append(video.id)
            if video.has_audio and audio:
                raise MediaError(
                    "This video already includes audio. "
                    "Choose a video-only format to pair tracks."
                )
            if video.has_audio and selection.audio is None:
                raise MediaError(
                    "This format includes audio; "
                    "select a video-only format for silent video."
                )
            if not video.has_audio:
                if selection.audio == "auto":
                    candidates = [
                        fmt
                        for fmt in info.formats
                        if fmt.has_audio and not fmt.has_video
                    ]
                    matching = [
                        fmt
                        for fmt in candidates
                        if fmt.language.split("-")[0]
                        == video.language.split("-")[0]
                    ]
                    if video.language and any(
                        fmt.language for fmt in candidates
                    ):
                        candidates = matching
                    audio = (matching or candidates or [None])[-1]
                    if audio is None:
                        raise MediaError(
                            "No matching audio-only track; choose a combined "
                            "version or explicitly disable audio."
                        )
                if audio:
                    formats.append(audio.id)
                    needs_ffmpeg = True
        elif selection.audio is not None:
            if selection.audio == "auto":
                candidates = [
                    fmt
                    for fmt in info.formats
                    if fmt.has_audio and not fmt.has_video
                ]
                candidates = candidates or [
                    fmt for fmt in info.formats if fmt.has_audio
                ]
                audio = candidates[-1] if candidates else None
            if audio is None:
                raise MediaError("No audio track is available.")
            formats.append(audio.id)
            if audio.has_video:
                needs_ffmpeg = True
                options["postprocessors"] = [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "best"}
                ]
        tracks = {track.key: track for track in info.subtitles}
        selected: list[SubtitleTrack] = []
        for key in selection.subtitles:
            if key not in tracks:
                raise MediaError(
                    "Selected subtitles are no longer available; "
                    "refresh the list."
                )
            selected.append(tracks[key])
        # yt-dlp accepts one subtitle format and source per language per job.
        # Preserve all chosen variants with separate subtitle-only jobs in
        # download(); keep the primary job free of implicit subtitle picks.
        if not formats and not selected:
            raise MediaError("Select video, audio or subtitles to download.")
        if needs_ffmpeg and not shutil.which("ffmpeg"):
            raise MediaError(
                "ffmpeg is required to merge tracks or extract audio."
            )
        options["skip_download"] = not formats
        if formats:
            options["format"] = "+".join(formats)
            if len(formats) > 1:
                options["merge_output_format"] = "mkv"
        # Subtitle choices should not duplicate an otherwise identical video.
        identity = f"{formats!r}:{bool(video)}"
        fingerprint = hashlib.sha256(identity.encode()).hexdigest()[:10]
        options["outtmpl"] = f"%(title).160B [%(id)s] [{fingerprint}].%(ext)s"
        return options
