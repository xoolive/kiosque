from functools import lru_cache
from urllib.parse import unquote

from bs4 import BeautifulSoup

from ..core.website import Website
from ..core.session import session


class MondeDiplomatique(Website):

    base_url = "https://www.monde-diplomatique.fr/"
    login_url = "https://lecteurs.mondediplo.net/?page=connexion_sso"
    alias = ["diplomatique", "diplo"]

    @property
    def login_dict(self):
        credentials = self.credentials
        assert credentials is not None

        c = session.get(self.login_url)
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")
        attrs = dict(name="formulaire_action_args")
        form_id = e.find("input", attrs=attrs).attrs["value"]

        return {
            "formulaire_action": "identification_sso",
            "formulaire_action_args": form_id,
            "retour": "https://www.monde-diplomatique.fr/",
            "site_distant": "https://www.monde-diplomatique.fr/",
            "valider": "Valider",
            "email": credentials["username"],
            "mot_de_passe": credentials["password"],
        }

    @lru_cache()
    def latest_issue_url(self):

        c = session.get(self.base_url)
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")

        current = e.find("a", attrs={"id": "entree-numero"}).attrs["href"]

        c = session.get(self.base_url + current)
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")

        attrs = {"class": "format PDF"}
        url = e.find("div", attrs=attrs).find("a").attrs["href"]
        return self.base_url + url

    def file_name(self, c) -> str:
        return unquote(
            c.headers["Content-Disposition"]
            .split(";")[1]
            .split("=")[1]
            .strip('"')
        )

    def description(self, url):
        e = self.bs4(url)
        node = e.find("meta", {"name": "description"})
        if node is None:
            return None
        return node.attrs.get("content", None)

    def date(self, url):
        e = self.bs4(url)
        node = e.find("meta", {"property": "article:published_time"})
        if node is None:
            return None
        date = node.attrs.get("content", None)
        if date is None:
            return None
        return date[:10]

    def author(self, url: str):
        e = self.bs4(url)
        node = e.find("meta", {"property": "article:author"})
        if node is None:
            return None
        return node.attrs.get("content", None)

    def article(self, url):
        e = self.bs4(url)
        return e.find("div", {"class": "texte"})

    def clean(self, article):
        article = super().clean(article)
        article.name = "article"

        for elem in article.find_all("figure"):
            elem.decompose()
        for elem in article.find_all("div"):
            elem.decompose()

        for elem in article.find_all("h3"):
            elem.attrs.clear()
        for elem in article.find_all("span"):
            elem.attrs.clear()
        for elem in article.find_all("small"):
            elem.decompose()
        for elem in article.find_all("a"):
            elem.decompose()

        return article
