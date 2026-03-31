from __future__ import annotations

import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import ClassVar

from ..core.client import get_with_retry
from ..core.website import Website

_FX_API = "https://api.fxtwitter.com"


@lru_cache(maxsize=128)
def _fetch(url: str) -> dict:
    match = re.search(r"(?:x|twitter)\.com/([^/?]+)/status/(\d+)", url)
    if not match:
        raise ValueError(f"Cannot parse X/Twitter URL: {url}")
    username, status_id = match.group(1), match.group(2)
    response = get_with_retry(
        f"{_FX_API}/{username}/status/{status_id}",
        headers={"Accept-Encoding": "identity"},
    )
    response.raise_for_status()
    data = response.json()
    if data.get("code") != 200:
        raise Exception(
            f"fxtwitter API error {data.get('code')}: {data.get('message')}"
        )
    return data["tweet"]


def _render_note(article: dict) -> str:
    blocks = article["content"]["blocks"]
    entity_map = {
        str(e["key"]): e["value"] for e in article["content"]["entityMap"]
    }
    media_by_id = {
        m["media_id"]: m["media_info"]["original_img_url"]
        for m in article.get("media_entities", [])
        if "original_img_url" in m.get("media_info", {})
    }

    parts = []
    for block in blocks:
        if block["type"] == "unstyled":
            text = block["text"].strip()
            if text:
                parts.append(text)
        elif block["type"] == "atomic":
            ranges = block.get("entityRanges", [])
            if not ranges:
                continue
            entity = entity_map.get(str(ranges[0]["key"]))
            if entity is None:
                continue
            etype = entity["type"]
            edata = entity["data"]
            if etype == "TWEET":
                tid = edata.get("tweetId", "")
                parts.append(
                    f"> [Embedded tweet](https://x.com/i/status/{tid})"
                )
            elif etype == "MEDIA":
                caption = edata.get("caption", "")
                for item in edata.get("mediaItems", []):
                    img_url = media_by_id.get(item.get("mediaId"), "")
                    if img_url:
                        parts.append(f"![{caption}]({img_url})")
    return "\n\n".join(parts)


def _fetch_thread(url: str) -> list[dict]:
    """Starting from any tweet, walk backwards through self-replies to the root.
    Returns the full chain in chronological order (root first)."""
    tweet = _fetch(url)
    chain = [tweet]
    author = tweet["author"]["screen_name"].lower()

    current = tweet
    while (
        current.get("replying_to_status")
        and current.get("replying_to", "").lower() == author
    ):
        parent_url = f"https://x.com/{tweet['author']['screen_name']}/status/{current['replying_to_status']}"
        current = _fetch(parent_url)
        chain.append(current)

    chain.reverse()
    return chain


def _render_thread(tweets: list[dict]) -> str:
    parts = []
    for i, tweet in enumerate(tweets):
        text = tweet.get("text", "").strip()
        if text:
            parts.append(text)
        for photo in tweet.get("media", {}).get("photos", []):
            parts.append(f"![]({photo['url']})")
        for video in tweet.get("media", {}).get("videos", []):
            parts.append(f"[Video]({video.get('url', '')})")
        if i < len(tweets) - 1:
            parts.append("---")
    return "\n\n".join(parts)


class Twitter(Website):
    base_url = "https://x.com/"
    alias: ClassVar[list[str]] = ["twitter", "x"]

    def _root(self, url: str) -> dict:
        """Return the root tweet of the thread (or the tweet itself)."""
        tweet = _fetch(url)
        if tweet.get("article"):
            return tweet
        return _fetch_thread(url)[0]

    def title(self, url: str) -> str | None:
        tweet = self._root(url)
        if tweet.get("article"):
            return tweet["article"].get("title")
        return f"Tweet by @{tweet['author']['screen_name']}"

    def author(self, url: str) -> str | None:
        return self._root(url)["author"]["name"]

    def date(self, url: str) -> str | None:
        ts = self._root(url).get("created_timestamp")
        if ts:
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime(
                "%Y-%m-%d"
            )
        return None

    def description(self, url: str) -> str | None:
        tweet = self._root(url)
        if tweet.get("article"):
            return tweet["article"].get("preview_text")
        text = tweet.get("text", "")
        return text[:200] if text else None

    def content(self, url: str) -> str:
        tweet = _fetch(url)
        if tweet.get("article"):
            return _render_note(tweet["article"])
        return _render_thread(_fetch_thread(url))

    def full_text(self, url: str) -> str:
        return f"{self.header(url)}\n{self.content(url)}"

    def write_text(self, url: str, filename: Path | None = None) -> None:
        if filename is None:
            tweet = _fetch(url)
            if tweet.get("article") and tweet["article"].get("title"):
                slug = re.sub(
                    r"[^a-z0-9]+", "-", tweet["article"]["title"].lower()
                ).strip("-")
                filename = Path(f"{self.date(url)}-{slug}")
            else:
                filename = Path(f"{self.date(url)}-{url.split('/')[-1]}")
        super().write_text(url, filename)
