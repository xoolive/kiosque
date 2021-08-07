from __future__ import annotations

from functools import lru_cache

from bs4 import BeautifulSoup

from ..core.session import session
from ..core.website import Website


class CourrierInternational(Website):

    base_url = "https://www.courrierinternational.com/"
    login_url = base_url + "login?destination=node/6"
    alias = ["courrier"]

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
            "form_id": "user_login",
            "op": "Se connecter",
            "name": credentials["username"],
            "pass": credentials["password"],
        }

    @lru_cache()
    def latest_issue_url(self):
        c = session.get(self.base_url + "magazine")
        c.raise_for_status()
        e = BeautifulSoup(c.content, features="lxml")

        x = e.find("article", attrs={"class": "item hebdo"})

        c = session.get(self.base_url + x.find("a").attrs["href"])
        c.raise_for_status()
        e = BeautifulSoup(c.content, features="lxml")
        attrs = {"class": "issue-download"}

        return e.find("a", attrs=attrs).attrs["href"]

    def article(self, url: str):
        e = self.bs4(url)
        return e.find("div", {"class", "article-text"})

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

    def clean(self, article):
        article = super().clean(article)
        article.name = "article"
        for elem in article.find_all("h3"):
            elem.attrs.clear()
        for elem in article.find_all("div"):
            elem.decompose()
        for elem in article.find_all(
            "span", {"class", "empty-author-name-short"}
        ):
            elem.decompose()
        return article
