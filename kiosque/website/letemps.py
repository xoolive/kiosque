from typing import ClassVar

from ..core.website import Website


class LeTemps(Website):
    base_url = "https://www.letemps.ch/"

    date_meta: ClassVar = {"name": ["article:published_time"]}

    clean_nodes: ClassVar = ["span"]
    decompose_nodes: ClassVar = ["div"]

    def author(self, url):
        e = self.bs4(url)
        return e.find("a", {"class": "author-profile"}).text.strip()

    def article(self, url):
        e = self.bs4(url)
        article = e.find("div", {"class": "body_content"})
        return article.find("div")
