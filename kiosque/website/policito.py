from typing import ClassVar

import pandas as pd
from bs4 import BeautifulSoup

from ..core.website import Website


class Politico(Website):
    base_url = "https://www.politico.com/"

    article_node = "div", {"class": "page-content"}
    clean_nodes: ClassVar = [
        ("div", {"class": "story-meta"}),
        "aside",
        "header",
    ]

    def author(self, url):
        e = self.bs4(url)
        return (
            e.find("p", {"class": "story-meta__authors"})
            .find("span")
            .text.strip()
        )

    def date(self, url):
        e = self.bs4(url)
        date = e.find("meta", {"name": "build"}).attrs["content"]
        return f"{pd.Timestamp(date):%Y-%m-%d}"

    def clean(self, article):
        article = super().clean(article)

        new_article = BeautifulSoup("<article></article>", features="lxml")

        for elem in article.find_all("p"):
            new_article.append(elem)

        return new_article


class Politico_eu(Politico):
    base_url = "https://www.politico.eu/"

    article_node = "div", {"class": "article__content"}
    clean_nodes: ClassVar = ["div", "figure"]

    def author(self, url):
        e = self.bs4(url)
        return e.find("div", {"class": "authors"}).find("a").text.strip()

    def article(self, url):
        article = super().article(url)
        return article.find(self.article_node[0], self.article_node[1])  # type: ignore
