import json

import requests

from ..core.session import session
from ..core.website import Website


class LesEchos(Website):
    base_url = "https://www.lesechos.fr/"
    login_url = "https://api.lesechos.fr/api/v1/auth/login"

    @property
    def login_dict(self):
        credentials = self.credentials
        assert credentials is not None
        return dict(
            email=credentials["username"], password=credentials["password"]
        )

    def login(self):
        # Not sure whether it is a requests bug, but some cookies seem to
        # require manual settings...

        login_response = super().login()
        if login_response is None:
            return

        cookies_as_json = login_response.json()

        for cookie in cookies_as_json["cookies"]:
            cookie_obj = requests.cookies.create_cookie(
                domain="lesechos.fr",
                name=cookie["name"],
                value=str(cookie["value"]),
            )
            session.cookies.set_cookie(cookie_obj)

        cookie_obj = requests.cookies.create_cookie(
            domain="lesechos.fr",
            name="authentication",
            value=json.dumps(cookies_as_json),
        )
        session.cookies.set_cookie(cookie_obj)

    def author(self, url):
        article = self.article(url)
        author = article.previous_sibling.previous_sibling
        if author is not None:
            return author.text[4:]
        author = article.next_sibling
        if author is not None:
            return author.text
        return None

    article_node = "section"

    def article(self, url):
        article = super().article(url)
        return article.find("div", {"class": "post-paywall"})

    clean_nodes = ["div"]
    clean_attributes = ["h3"]

    def clean(self, article):
        article = super().clean(article)
        for elem in article.find_all(["a", "img"]):
            del elem.attrs["class"]
        return article
