import logging
import urllib
from datetime import datetime

from bs4 import BeautifulSoup

from ..core.session import session
from ..core.website import Website


class AviationWeek(Website):
    base_url = "https://aviationweek.com/"
    login_url = "https://aviationweek.auth0.com/login"

    title_meta = {"name": "title"}
    description_meta = {"name": "description"}

    clean_nodes = [("div", {"class": ["dfp-ad", "dfp-tag"]})]

    def login(self):
        credentials = self.credentials
        assert credentials is not None

        logging.info(f"Logging in at {self.login_url}")

        c = session.get("https://aviationweek.auth0.com/login")
        c.raise_for_status()

        index = c.url.find("?") + 1
        url_params = urllib.parse.parse_qs(c.url[index:])

        post_url = "https://aviationweek.auth0.com/usernamepassword/login"

        payload = {
            "client_id": url_params["client"][0],
            "redirect_uri": "https://aviationweek.com/auth0/callback",
            "tenant": "aviationweek",
            "response_type": "code",
            "scope": "openid email profile",
            "state": url_params["state"][0],
            "_intstate": "deprecated",
            "username": credentials["username"],
            "password": credentials["password"],
            "connection": "Username-Password-Authentication",
        }

        c = session.post(post_url, data=payload)
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")
        c = session.post(
            "https://aviationweek.auth0.com/login/callback",
            data=dict(
                (elt.attrs["name"], elt.attrs["value"])
                for elt in e.find_all("input")
                if elt.get("name")
            ),
        )
        c.raise_for_status()
        self.__class__.connected = True
        return c

    def article(self, url):
        e = self.bs4(url)
        return e.find("article").find("div", {"class": "article__body"})

    def clean(self, article):
        article = super().clean(article)
        article = article.find("div")
        article.name = "article"
        return article

    def date(self, url):
        e = self.bs4(url)
        date_node = e.find("span", {"class": "article__date"})
        if date_node is None:
            return None
        date = datetime.strptime(date_node.text, "%B %d, %Y")
        return f"{date:%Y-%m-%d}"

    def author(self, url):
        e = self.bs4(url)
        author = e.find("a", {"class": "author--teaser__name"})
        if author is not None:
            return author.text
