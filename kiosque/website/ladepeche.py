from ..core.website import Website


class LaDepeche(Website):
    base_url = "https://www.ladepeche.fr/"

    def description(self, url):
        e = self.bs4(url)
        p = e.find("p", {"class": "article-full__chapo"})
        for elem in p.find_all("span"):
            elem.decompose()
        return p.text.strip()

    def date(self, url):
        e = self.bs4(url)
        return e.find("time").attrs["content"][:10]

    def article(self, url):
        e = self.bs4(url)
        article = e.find("div", {"class": "article-full__body-content"})
        return article

    def clean(self, article):
        article = super().clean(article)

        for elem in article.find_all("h2"):
            elem.attrs.clear()

        for elem in article.find_all("div"):
            elem.decompose()

        return article
