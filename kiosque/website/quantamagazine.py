from ..core.website import Website


class QuantaMagazine(Website):
    base_url = "https://www.quantamagazine.org/"

    article_node = "div", {"class": "post__content__section"}
    clean_nodes = ["div"]

    def article(self, url):
        article = super().article(url)
        return article.find("div")

    def author(self, url):
        e = self.bs4(url)
        author_node = e.find("div", {"class": "sidebar__author"}).find("h3")
        if author_node is not None:
            return author_node.text
