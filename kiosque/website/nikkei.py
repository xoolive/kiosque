from ..core.website import Website


class Nikkei(Website):
    base_url = "https://www.nikkei.com"

    header_entries = ["title", "date", "url"]

    def article(self, url):
        return self.bs4(url).find("article").find("section")


class NikkeiAsia(Website):
    base_url = "https://asia.nikkei.com/"

    article_node = ("div", {"class": "ezrichtext-field"})
    clean_nodes = ["div"]
