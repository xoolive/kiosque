from functools import lru_cache
from urllib.parse import unquote

from bs4 import BeautifulSoup

from ..core.website import Website
from ..core.session import session


class MondeDiplomatique(Website):
    base_url = "https://www.monde-diplomatique.fr/"
    # login_url = "https://lecteurs.mondediplo.net/?page=connexion_sso"
    login_url = "https://www.monde-diplomatique.fr/load_mon_compte"
    alias = ["diplomatique", "diplo"]

    description_meta = {"name": ["description"]}

    article_node = ("div", {"class": "texte"})

    clean_nodes = ["figure", "div", "small", "a"]
    clean_attributes = ["h3", "span"]

    @property
    def login_dict(self):
        credentials = self.credentials
        assert credentials is not None

        c = session.get(self.base_url)
        c.raise_for_status()

        c = session.post(
            "https://www.monde-diplomatique.fr/load_mon_compte",
            dict(
                retour="https://www.monde-diplomatique.fr/",
                erreur_connexion="",
                triggerAjaxLoad="",
            ),
        )
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")
        formulaire_action = e.find(
            "input", attrs={"name": "formulaire_action"}
        ).attrs["value"]
        formulaire_action_args = e.find(
            "input", attrs={"name": "formulaire_action_args"}
        ).attrs["value"]
        retour = e.find("input", attrs={"name": "retour"}).attrs["value"]
        _jeton = e.find("input", attrs={"name": "_jeton"}).attrs["value"]

        return {
            "formulaire_action": formulaire_action,
            "formulaire_action_args": formulaire_action_args,
            "retour": retour,
            "_jeton": _jeton,
            "valider": "Valider",
            "email": credentials["username"],
            "mot_de_passe": credentials["password"],
            "email_nobot": "",
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
