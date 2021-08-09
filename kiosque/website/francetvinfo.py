from ..core.website import Website


class FranceTVInfo(Website):
    base_url = "https://www.francetvinfo.fr/"

    article_node = ("div", {"id": "col-middle"})

    clean_nodes = ["div", "figure", "aside"]
    clean_attributes = ["h2"]

    def description(self, url):
        e = self.bs4(url)
        return e.find("p", {"class": "chapo"}).text.strip()

    def author(self, url):
        e = self.bs4(url)
        return e.find("a", {"class": "author"}).text.strip()
