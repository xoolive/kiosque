from typing import ClassVar

from ..core.website import Website


class Mediapart(Website):
    base_url = "https://www.mediapart.fr/"
    login_url = "https://auth.mediapart.fr/login"

    author_meta: ClassVar = {"name": ["author"]}

    clean_nodes: ClassVar = ["div"]

    @property
    def login_dict(self):
        credentials = self.credentials
        assert credentials is not None

        return {
            "username": credentials["username"],
            "password": credentials["password"],
            "origin_url": f"{self.base_url}login",
            "destination_url": self.base_url,
        }

    def article(self, url):
        e = self.bs4(url)
        article = e.find("div", {"class": "content-article"})

        # if not logged in
        embedded = article.find("div", {"class": "content-article"})
        if embedded is not None:
            article = embedded

        # if logged in
        embedded = article.find("div", {"class": "page-pane"})
        if embedded is not None:
            article = embedded

        return article
