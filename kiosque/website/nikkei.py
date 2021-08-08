from ..core.website import Website


class Nikkei(Website):
    base_url = "https://asia.nikkei.com/"

    def article(self, url):
        e = self.bs4(url)
        return e.find("div", {"class": "ezrichtext-field"})

    def clean(self, article):
        article = super().clean(article)
        for elem in article.find_all("div"):
            elem.decompose()
        return article
