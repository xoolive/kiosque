from __future__ import annotations

import copy
import logging
import re
from importlib import import_module
from functools import lru_cache
from pathlib import Path
from typing import Any, Type

import pypandoc
from bs4 import BeautifulSoup
from bs4.element import Tag
import requests

from .config import config_dict
from .session import session


class Website:

    known_websites: list[Type[Website]] = list()

    alias: list[str] = list()
    base_url: str
    login_url: str
    connected: bool = False

    url_translation: dict[str, str] = dict()

    # meta fields
    author_meta: dict[str, list[str]] = {
        "property": [
            "og:article:author",
            "article:author",
        ]
    }

    date_meta: dict[str, list[str]] = {
        "property": [
            "og:article:published_time",
            "article:published_time",
            "date",
        ]
    }

    description_meta: dict[str, list[str]] = {
        "property": [
            "og:description",
            "description",
        ]
    }

    article_node: str | tuple[str, dict[str, str]]

    clean_nodes: list[str] = []
    clean_attributes: list[str] = []

    header_entries = ["title", "author", "date", "url", "description"]

    def __init_subclass__(cls) -> None:
        cls.known_websites.append(cls)

    def __init__(self) -> None:
        self.credentials = config_dict.get(self.base_url, None)

    @classmethod
    def instance(cls, url: str) -> Website:
        url = url.replace("http://", "https://")

        # -- First check if the website is already created --
        for website in cls.known_websites:
            if url.startswith(website.base_url):
                return website()

        # -- Otherwise guess which file to import --
        pat = re.compile(r'\s+base_url = "(.*)"')
        for x in (Path(__file__).parent.parent / "website").glob("*.py"):
            for line in x.read_text().split("\n"):
                match = pat.match(line)
                if match and url.startswith(match.group(1)):
                    module_name = f"kiosque.website.{x.stem}"
                    logging.info(f"Import {module_name}")
                    globals()[module_name] = import_module(module_name)
                    return cls.known_websites[-1]()

        # -- Attempt to access the website, and fetch for the real URL --
        c = session.get(url)
        c.raise_for_status()
        e = BeautifulSoup(c.content, features="lxml")
        new_url = e.find("meta", {"property": "og:url"}).attrs["content"]
        if url != new_url:
            cls.url_translation[url] = new_url
            return cls.instance(new_url)

        raise ValueError("Unsupported URL")

    # -- Credentials (if any) --

    @property
    def login_dict(self) -> dict[str, Any]:
        return {}

    def login(self) -> requests.Response:
        c = session.get(self.base_url)
        c.raise_for_status()

        login_dict = self.login_dict
        if self.connected or login_dict == {}:
            return

        c = session.post(self.login_url, data=login_dict)
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
        c = session.get(url)
        c.raise_for_status()
        return BeautifulSoup(c.content, features="lxml")

    def title(self, url: str) -> str | None:
        e = self.bs4(url)
        node = e.find("meta", {"property": "og:title"})
        if node is None:
            return None
        return node.attrs.get("content", None)

    def author(self, url: str) -> str | None:
        e = self.bs4(url)
        node = e.find("meta", self.author_meta)
        if node is None:
            return None
        return node.attrs.get("content", None)

    def date(self, url: str) -> str | None:
        e = self.bs4(url)
        node = e.find("meta", self.date_meta)
        if node is None:
            return None
        date = node.attrs.get("content", None)
        if date is None:
            return None
        return date[:10]

    def url(self, url: str) -> str:
        return url

    def description(self, url: str) -> str | None:
        e = self.bs4(url)
        node = e.find("meta", self.description_meta)
        if node is None:
            return None
        return node.attrs.get("content", None)

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
            return article
        raise NotImplementedError

    def clean(self, article: Tag) -> Tag:
        article = copy.copy(article)
        article.attrs.clear()
        article.name = "article"

        for id in self.clean_attributes:
            if isinstance(id, str):
                for elem in article.find_all(id):
                    elem.attrs.clear()
            elif isinstance(id, tuple):
                for elem in article.find_all(*id):
                    elem.attrs.clear()

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
        return pypandoc.convert_text(article, "md", format="html")

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
        raise NotImplementedError()

    def file_name(self, c) -> str:
        if not self.connected:
            self.login()
        url = self.latest_issue_url()
        return Path(url).name

    def get_latest_issue(self):
        if self.latest_issue is not None:
            return self.latest_issue
        if not self.connected:
            self.login()
        url = self.latest_issue_url()
        c = session.get(url)
        return c

    def save_latest_issue(self):
        c = self.get_latest_issue()
        full_path = Path(".") / self.file_name(c)
        full_path.write_bytes(c.content)
        print(f"File written: {full_path}")
