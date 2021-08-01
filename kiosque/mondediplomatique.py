from functools import lru_cache
from urllib.parse import unquote

from bs4 import BeautifulSoup

from .download import Download


class MondeDiplomatique(Download):

    base_url = "https://www.monde-diplomatique.fr/"
    login_url = "https://lecteurs.mondediplo.net/?page=connexion_sso"

    def login_dict(self):
        c = self.session.get(self.login_url)
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
            **self.credentials,
        }

    @lru_cache()
    def latest_issue_url(self):

        c = self.session.get(self.base_url)
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")

        current = e.find("a", attrs={"id": "entree-numero"}).attrs["href"]

        c = self.session.get(self.base_url + current)
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
