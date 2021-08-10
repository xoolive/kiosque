from ..core.website import Website


class LeFigaro(Website):
    base_url = "https://www.lefigaro.fr/"

    article_node = "div", {"class": "fig-body"}
    clean_nodes = ["div", "svg", ("p", {"class": "fig-body-link"})]

    def author(self, url):
        e = self.bs4(url)
        author = e.find("a", {"class": "fig-content-metas__author"})
        if author is not None:
            return author.text

    def date(self, url):
        e = self.bs4(url)
        return e.find("time").attrs["datetime"][:10]
