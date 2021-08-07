from ..core.website import Website


class FranceCulture(Website):
    base_url = "https://www.franceculture.fr/"

    def date(self, url):
        e = self.bs4(url)
        node = e.find("meta", {"property": "article:published_time"})
        if node is None:
            return None
        date = node.attrs.get("content", None)
        if date is None:
            return None
        return date[:10]

    def author(self, url):
        author = super().author(url)
        if author is not None:
            return author

        e = self.bs4(url)
        node = e.find("div", {"class": "heading-zone-title-owner"})
        if node is None:
            return None

        author = node.find("a")
        if author is None:
            return None

        return author.text  # type: ignore

    def article(self, url):
        e = self.bs4(url)
        return e.find("div", {"class": "content-body"})

    def clean(self, article):
        article = super().clean(article)
        article.name = "article"
        for elem in article.find_all("div"):
            elem.decompose()
        for elem in article.find_all("figure"):
            elem.decompose()
        for elem in article.find_all("aside"):
            elem.decompose()
        return article
