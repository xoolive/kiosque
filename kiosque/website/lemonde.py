from bs4 import BeautifulSoup

from ..core.website import Website
from ..core.session import session


class LeMonde(Website):

    base_url = "https://www.lemonde.fr/"
    login_url = "https://secure.lemonde.fr/sfuser/connexion"
    alias = ["lemonde"]

    clean_nodes = [
        "figure",
        (
            "section",
            {"class": ["catcher", "author", "article__reactions"]},
        ),
        ("div", {"class": "dfp__inread"}),
    ]
    clean_attributes = ["h2"]

    @property
    def login_dict(self):
        credentials = self.credentials
        assert credentials is not None

        c = session.get(self.login_url)
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")
        attrs = dict(name="connection[_token]")
        token = e.find("input", attrs=attrs).attrs["value"]

        return {
            "connection[mail]": credentials["username"],
            "connection[password]": credentials["password"],
            "connection[stay_connected]": 1,
            "connection[save]": "",
            "connection[newsletters]": [],
            "connection[_token]": token,
        }

    def article(self, url):
        e = self.bs4(url)
        article = e.find("article", attrs={"class": "article__content"})
        if article is None:
            article = e.find("section", attrs={"class": "article__content"})
        else:
            embedded = article.find(
                "section", attrs={"class": "article__content"}
            )
            if embedded is not None:
                article = embedded

        return article

    def clean(self, article):
        article = super().clean(article)

        for elem in article.find_all("h3"):
            elem.name = "blockquote"
            elem.attrs.clear()

        return article
