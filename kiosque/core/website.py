from __future__ import annotations

import copy
import logging
import re
from datetime import datetime
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Any, ClassVar

import httpx
import pypandoc
from bs4 import BeautifulSoup
from bs4._typing import _StrainableAttributes
from bs4.element import Tag

from .client import client, get_with_retry, post_with_retry
from .config import config_dict


class Website:
    known_websites: ClassVar[list[type["Website"]]] = list()
    _module_cache: ClassVar[dict[str, str]] = {}  # Cache base_url -> module

    alias: ClassVar[list[str]] = list()
    base_url: str
    login_url: str
    connected: bool = False

    credentials: None | dict[str, str]

    url_translation: ClassVar[dict[str, str]] = dict()

    # meta fields
    title_meta: ClassVar[_StrainableAttributes] = {
        "property": [
            "og:title",
            "title",
        ]
    }

    author_meta: ClassVar[_StrainableAttributes] = {
        "property": [
            "og:article:author",
            "article:author",
        ]
    }

    date_meta: ClassVar[_StrainableAttributes] = {
        "property": [
            "og:article:published_time",
            "article:published_time",
            "og:article:updated_time",
            "og:updated_time",
            "date",
        ]
    }

    description_meta: ClassVar[_StrainableAttributes] = {
        "property": [
            "og:description",
            "description",
        ]
    }

    article_node: str | tuple[str, _StrainableAttributes]

    clean_nodes: ClassVar[list[str | tuple[str, _StrainableAttributes]]] = []
    clean_attributes: ClassVar[
        list[str | tuple[str, _StrainableAttributes]]
    ] = []

    header_entries: ClassVar[list[str]] = [
        "title",
        "author",
        "date",
        "url",
        "description",
    ]

    def __init_subclass__(cls) -> None:
        cls.known_websites.append(cls)

    def __init__(self) -> None:
        self.credentials = config_dict.get(self.base_url, None)

    @classmethod
    def _build_module_cache(cls) -> None:
        """Build cache of base_url -> module_name and alias mappings."""
        if cls._module_cache:
            return  # Already cached

        base_url_pat = re.compile(r'\s+base_url = "(.*)"')
        alias_pat = re.compile(r"\s+alias.*=.*\[(.*)\]")
        website_dir = Path(__file__).parent.parent / "website"

        for x in website_dir.glob("*.py"):
            if x.stem.startswith("_"):
                continue

            content = x.read_text()
            module_name = f"kiosque.website.{x.stem}"

            # Extract base_url
            for line in content.split("\n"):
                match = base_url_pat.match(line)
                if match:
                    cls._module_cache[match.group(1)] = module_name
                    break

            # Extract aliases
            for line in content.split("\n"):
                match = alias_pat.match(line)
                if match:
                    # Parse alias list: ["foo", "bar"] or ['foo', 'bar']
                    aliases_str = match.group(1)
                    # Simple parsing: extract strings between quotes
                    alias_items = re.findall(
                        r'["\']([^"\']+)["\']', aliases_str
                    )
                    for alias in alias_items:
                        cls._module_cache[alias] = module_name
                    break

        logging.debug(
            f"Built module cache with {len(cls._module_cache)} entries"
        )

    @classmethod
    def instance(cls, url_or_alias: str) -> Website:
        url_or_alias = url_or_alias.replace("http://", "https://")

        # -- First check if the website is already created --
        for website in cls.known_websites:
            if (
                url_or_alias.startswith(website.base_url)
                or url_or_alias in website.alias
            ):
                return website()

        # -- Otherwise use cache to find the module --
        cls._build_module_cache()

        # Check for exact alias match or URL prefix match
        for key, module_name in cls._module_cache.items():
            if url_or_alias == key or url_or_alias.startswith(key):
                logging.info(f"Import {module_name}")
                globals()[module_name] = import_module(module_name)
                return cls.known_websites[-1]()

        # -- Attempt to access the website, and fetch for the real URL --
        c = get_with_retry(url_or_alias)
        c.raise_for_status()
        e = BeautifulSoup(c.content, features="lxml")
        new_url_node = e.find("meta", {"property": "og:url"})
        new_url: str = new_url_node.attrs["content"] if new_url_node else None  # type: ignore
        if url_or_alias != new_url and new_url is not None:
            cls.url_translation[url_or_alias] = new_url
            return cls.instance(new_url)

        raise ValueError(
            f"Unsupported URL: {url_or_alias}\n"
            "This website is not currently supported by kiosque.\n"
            "To see supported websites, check the documentation or "
            "look in the kiosque/website/ directory."
        )

    # -- Credentials (if any) --

    @property
    def login_dict(self) -> dict[str, Any]:
        return {}

    def login(self) -> httpx.Response | None:
        c = get_with_retry(self.base_url)
        c.raise_for_status()

        logging.info(f"Logging in at {self.login_url}")

        login_dict = self.login_dict
        if self.connected or login_dict == {}:
            return None

        c = post_with_retry(
            self.login_url,
            data=login_dict,
            headers={
                **client.headers,
                "Origin": self.base_url,
                "Referer": self.base_url,
            },
        )
        c.raise_for_status()
        self.__class__.connected = True
        return c

    # -- Metadata --

    @lru_cache()
    def bs4(self, url: str) -> BeautifulSoup:
        if not self.connected and self.credentials is not None:
            self.login()
        # Just in case this URL has been redirected...
        url = self.url_translation.get(url, url)
        c = get_with_retry(url)
        c.raise_for_status()
        return BeautifulSoup(c.content, features="lxml")

    def title(self, url: str) -> str | None:
        e = self.bs4(url)
        node = e.find("meta", self.title_meta)
        if node is None:
            return None
        return node.attrs.get("content", None)  # type: ignore

    def author(self, url: str) -> str | None:
        e = self.bs4(url)
        node = e.find("meta", self.author_meta)
        if node is None:
            return None
        return node.attrs.get("content", None)  # type: ignore

    def date(self, url: str) -> str | None:
        e = self.bs4(url)
        node = e.find("meta", self.date_meta)
        if node is None:
            return None
        date = node.attrs.get("content", None)  # type: ignore
        if date is None:
            return None
        # Parse ISO 8601 datetime and format as YYYY-MM-DD
        try:
            dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            # If parsing fails, try to extract just the date part
            return date[:10] if len(date) >= 10 else date

    def url(self, url: str) -> str:
        return url

    def description(self, url: str) -> str | None:
        e = self.bs4(url)
        node = e.find("meta", self.description_meta)
        if node is None:
            return None
        text = node.attrs.get("content", None)  # type: ignore
        if text is None:
            return None
        return text.strip().split("\n")[0]

    def header(self, url: str) -> str:
        entries = "\n".join(
            f"{entry}: {getattr(self, entry)(url)}"
            for entry in self.header_entries
        )
        return f"---\n{entries}\n---\n"

    # -- Extract article body --

    def article(self, url: str) -> Tag:
        e = self.bs4(url)
        if isinstance(self.article_node, str):
            article = e.find(self.article_node)
        elif isinstance(self.article_node, tuple):
            article = e.find(*self.article_node)
        if article is not None:
            return article  # type: ignore
        raise NotImplementedError(
            f"Failed to extract article content from {url}. "
            "The article_node selector may need to be updated."
        )

    def clean(self, article: Tag) -> Tag:
        article = copy.copy(article)
        article.attrs.clear()
        article.name = "article"

        for id in self.clean_attributes:
            if isinstance(id, str):
                for elem in article.find_all(id):
                    elem.attrs.clear()  # type: ignore
            elif isinstance(id, tuple):
                for elem in article.find_all(*id):
                    elem.attrs.clear()  # type: ignore

        for id in self.clean_nodes:
            if isinstance(id, str):
                for elem in article.find_all(id):
                    elem.decompose()
            elif isinstance(id, tuple):
                for elem in article.find_all(*id):
                    elem.decompose()

        return article

    def content(self, url: str) -> str:
        article = self.article(url)
        article = self.clean(article)
        return pypandoc.convert_text(str(article), "md", format="html")

    def full_text(self, url: str) -> str:
        return f"{self.header(url)}\n{self.content(url)}"

    def write_text(self, url: str, filename: Path | None = None) -> None:
        if filename is None:
            basename = f"{url.split('/')[-1]}"
            filename = Path(f"{self.date(url)}-{basename}")
        filename = filename.with_suffix(".md")
        logging.warning(f"Export to {filename.absolute()}")
        filename.write_text(self.full_text(url))

    # -- Download PDF edition --

    def latest_issue_url(self) -> str:
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support downloading "
            "PDF issues. This feature is only available for select "
            "publications."
        )

    def file_name(self, c: httpx.Response) -> str:
        if not self.connected:
            self.login()
        url = self.latest_issue_url()
        return Path(url).name

    def get_latest_issue(self) -> httpx.Response:
        if not self.connected:
            self.login()
        url = self.latest_issue_url()
        c = get_with_retry(url)
        return c

    def save_latest_issue(self) -> None:
        c = self.get_latest_issue()
        full_path = (Path(".") / self.file_name(c)).with_suffix(".pdf")
        full_path.write_bytes(c.content)
        logging.info(f"File written: {full_path}")
