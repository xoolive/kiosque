from ..core.website import Website


class Nikkei(Website):
    base_url = "https://asia.nikkei.com/"

    def date(self, url):
        e = self.bs4(url)
        node = e.find("meta", {"name": "date"})
        if node is None:
            return None
        date = node.attrs.get("content", None)
        if date is None:
            return None
        return date[:10]

    def article(self, url):
        e = self.bs4(url)
        return e.find("div", {"class": "ezrichtext-field"})

    def clean(self, article):
        article = super().clean(article)
        article.name = "article"
        for elem in article.find_all("div"):
            elem.decompose()
        return article
