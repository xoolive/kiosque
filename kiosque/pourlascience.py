from functools import lru_cache
from urllib.parse import unquote

from bs4 import BeautifulSoup

from .download import Download


class PourLaScience(Download):

    base_url = "https://www.pourlascience.fr/"
    login_url = "https://sso.qiota.com/api/v1/login"

    def login_dict(self):

        c = self.session.get(self.base_url)
        c.raise_for_status()
        e = BeautifulSoup(c.content, features="lxml")
        form_url = e.find("a", attrs={"id": "connect_link"}).attrs["href"]
        c = self.session.get(form_url)
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")
        attrs = dict(name="client_id")
        client_id = e.find("input", attrs=attrs).attrs["value"]
        attrs = dict(name="referer")
        referer = e.find("input", attrs=attrs).attrs["value"]

        return {
            "response_type": "code",
            "scope": "email",
            "client_id": client_id,
            "redirect_uri": "https://www.pourlascience.fr/login",
            "error_uri": "https://connexion.groupepourlascience.fr",
            "referer": referer,
            "uri_referer": "https://www.pourlascience.fr/",
            **self.credentials,
        }

    def login(self):
        super().login()
        c = self.session.get(self.base_url + "login")
        c.raise_for_status()

    @lru_cache()
    def latest_issue_url(self):

        c = self.session.get("https://www.pourlascience.fr/")
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")

        current = e.find("li", attrs={"class": "magazine"})
        c = self.session.get(f"https:{current.find('a').attrs['href']}")
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")

        attrs = {"class": "btn btn-yellow", "id": "download"}
        url = e.find("a", attrs=attrs).attrs["href"]

        return f"{self.base_url}api{url}"

    def file_name(self, c) -> str:
        return unquote(
            c.headers["Content-Disposition"]
            .split(";")[2]
            .split("=")[1]
            .strip('"')[7:]
        )
