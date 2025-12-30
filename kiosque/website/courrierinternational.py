from __future__ import annotations

from functools import lru_cache
from typing import ClassVar

from bs4 import BeautifulSoup

from ..core.client import client
from ..core.website import Website


class CourrierInternational(Website):
    """Courrier International scraper.

    Note: Login is geo-blocked and returns 406 Not Acceptable for requests
    from outside France/Europe. To access from other regions, configure a
    SOCKS/HTTP proxy with a French/EU IP address in kiosque.conf:

    [proxy]
    url = socks5://localhost:1080

    See TROUBLESHOOTING.md for proxy setup instructions.
    """

    base_url = "https://www.courrierinternational.com/"
    login_url = "https://secure.courrierinternational.com/sfuser/connexion"

    alias: ClassVar = ["courrier"]

    article_node = ("div", {"class": "article-text"})

    clean_attributes: ClassVar = ["h3"]
    clean_nodes: ClassVar = [
        "div",
        ("span", {"class": "empty-author-name-short"}),
    ]

    header_entries: ClassVar = [
        "title",
        "author",
        "date",
        "url",
        "original_url",
        "description",
    ]

    @property
    def login_dict(self):
        credentials = self.credentials
        assert credentials is not None

        return {
            "email": credentials["username"],
            "password": credentials["password"],
            "submit-button": "Je me connecte",
        }

    @lru_cache()
    def latest_issue_url(self):
        c = client.get(self.base_url)
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")
        section = e.find("section", attrs={"class": "hebdo-section"})
        page_url = section.find("a").attrs["href"]

        c = client.get(page_url)
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")
        magazine = e.find("div", attrs={"class": "magazine-tools"})
        return magazine.find("a", attrs={"data-icon": "file-pdf"}).attrs["href"]

    def author(self, url: str):
        author = super().author(url)
        if author is not None:
            return author

        e = self.bs4(url)

        author_node = e.find("div", {"class", "author-name-short"})
        if author_node is not None:
            return author_node.text

        author_node = e.find("p", {"class": "author-name"})
        if author_node is not None:
            return author_node.text

        return ""

    def original_url(self, url: str) -> str | None:
        e = self.bs4(url)
        div = e.find("div", {"class", "article-url-origin"})
        if div is None:
            return None
        link = div.find("a")
        if link is None:
            return None
        return link.attrs["href"]
