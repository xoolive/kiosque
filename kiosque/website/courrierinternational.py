from functools import lru_cache

from bs4 import BeautifulSoup

from ..core.download import Download


class CourrierInternational(Download):

    base_url = "https://www.courrierinternational.com"
    login_url = base_url + "/login?destination=node/6"

    def login_dict(self):
        c = self.session.get(self.login_url)
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")
        attrs = dict(name="form_build_id")
        form_id = e.find("input", attrs=attrs).attrs["value"]

        return {
            "remember_me": "1",
            "form_build_id": form_id,
            "form_id": "user_login",
            "op": "Se connecter",
            **self.credentials,
        }

    @lru_cache()
    def latest_issue_url(self):
        c = self.session.get(self.base_url + "/magazine")
        c.raise_for_status()
        e = BeautifulSoup(c.content, features="lxml")

        x = e.find("article", attrs={"class": "item hebdo"})

        c = self.session.get(self.base_url + x.find("a").attrs["href"])
        c.raise_for_status()
        e = BeautifulSoup(c.content, features="lxml")
        attrs = {"class": "issue-download"}

        return e.find("a", attrs=attrs).attrs["href"]
