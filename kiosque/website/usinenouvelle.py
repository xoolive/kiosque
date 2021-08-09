from ..core.website import Website
from bs4 import BeautifulSoup


class UsineNouvelle(Website):
    base_url = "https://www.usinenouvelle.com/"
    login_url = "https://www.usinenouvelle.com/user/doLogin"

    date_meta = {"name": ["date.modified"]}

    article_node = ("div", {"class": "epAtcBody"})
    clean_nodes = ["section"]

    @property
    def login_dict(self):
        credentials = self.credentials
        assert credentials is not None
        return dict(
            username=credentials["username"],
            password=credentials["password"],
            submitConnexDejaAbo="Identifiez-vous",
        )

    def description(self, url):
        e = self.bs4(url)
        return e.find("div", {"class": "epArticleChapo"}).text.strip()

    def author(self, url):
        author = super().author(url)
        if author is not None:
            return author

        e = self.bs4(url)
        return e.find(
            "span", {"class": "epMetaData__content__infos-name"}
        ).text.strip()

    def clean(self, article):
        article = super().clean(article)

        for elem in article.find_all("span", {"class": "interTitre"}):
            elem.attrs.clear()
            elem.name = "h2"

        for elem in article.find_all("a", {"class": "lien-contextuel"}):
            elem.attrs.clear()
            elem.name = "span"

        new_article = BeautifulSoup("<article></article>")

        for elem in article.find_all("p"):
            new_article.append(elem)

        return new_article
