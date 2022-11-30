from __future__ import annotations

from functools import lru_cache

from bs4 import BeautifulSoup

from ..core.session import session
from ..core.website import Website


class CourrierInternational(Website):

    base_url = "https://www.courrierinternational.com/"
    login_url = base_url + "login?destination=<front>"
    alias = ["courrier"]

    article_node = ("div", {"class": "article-text"})

    clean_attributes = ["h3"]
    clean_nodes = ["div", ("span", {"class": "empty-author-name-short"})]

    header_entries = [
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

        c = session.get(self.login_url)
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")
        attrs = dict(name="form_build_id")
        form_id = e.find("input", attrs=attrs).attrs["value"]

        return {
            "remember_me": "1",
            "form_build_id": form_id,
            "form_id": "user_login_block",
            "op": "Se+connecter",
            "ci_promo_code_code": "",
            "name": credentials["username"],
            "pass": credentials["password"],
        }

    @lru_cache()
    def latest_issue_url(self):

        c = session.get(self.base_url)
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")
        section = e.find("section", attrs={"class": "hebdo-section"})
        page_url = section.find("a").attrs["href"]

        c = session.get(page_url)
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
