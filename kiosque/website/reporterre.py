from typing import ClassVar

from ..core.website import Website


class Reporterre(Website):
    base_url = "https://reporterre.net/"

    article_node = "article"
    clean_nodes: ClassVar = [
        "small",
        "dl",
        "div",
        "aside",
        ("span", {"class": "spip_note_ref"}),
    ]

    def author(self, url):
        e = self.bs4(url)
        author_node = e.find("a", {"class": "lienauteur"})
        if author_node is not None:
            return author_node.text

    def date(self, url):
        e = self.bs4(url)
        return e.find("span", {"class": "date"}).text.split(",")[0]

    def article(self, url):
        article = super().article(url)
        return article.find("div", {"class": "texte"})

    def clean(self, article):
        article = super().clean(article)

        for elem in article.find_all("a"):
            if "class" in elem.attrs:
                del elem.attrs["class"]

        return article
