from __future__ import annotations

from functools import lru_cache
from urllib.parse import unquote

from bs4 import BeautifulSoup

from ..core.client import client
from ..core.website import Website


class PourLaScience(Website):
    base_url = "https://www.pourlascience.fr/"
    login_url = "https://sso.qiota.com/api/v1/login"

    @property
    def login_dict(self) -> dict[str, str]:
        credentials = self.credentials
        assert credentials is not None

        c = client.get(self.base_url)
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")
        form_url = e.find("a", attrs={"id": "connect_link"}).attrs["href"]
        c = client.get(form_url)
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")
        client_id = e.find("input", {"name": "client_id"}).attrs["value"]  # type: ignore
        referer = e.find("input", {"name": "referer"}).attrs["value"]  # type: ignore

        return {
            "response_type": "code",
            "scope": "email",
            "client_id": client_id,
            "redirect_uri": "https://www.pourlascience.fr/login",
            "error_uri": "https://connexion.groupepourlascience.fr",
            "referer": referer,
            "uri_referer": "https://www.pourlascience.fr/",
            "email": credentials["username"],
            "password": credentials["password"],
        }

    def login(self):
        super().login()
        c = client.get(self.base_url + "login")
        c.raise_for_status()

    @lru_cache()
    def latest_issue_url(self):
        c = client.get("https://www.pourlascience.fr/archives")
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")
        current = e.find("div", attrs={"class": "book"})

        c = client.get(f"{current.find('a').attrs['href']}")
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")

        attrs = {"id": "download"}
        url = e.find("a", attrs=attrs).attrs["href"]

        return f"{self.base_url}api{url}"

    def file_name(self, c) -> str:
        return unquote(
            c.headers["Content-Disposition"]
            .split(";")[2]
            .split("=")[1]
            .strip('"')[7:]
        )
