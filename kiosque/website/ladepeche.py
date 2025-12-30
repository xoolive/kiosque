from typing import ClassVar

from ..core.website import Website


class LaDepeche(Website):
    base_url = "https://www.ladepeche.fr/"

    article_node = ("div", {"class": "article-full__body-content"})
    clean_nodes: ClassVar = ["div"]
    clean_attributes: ClassVar = ["h2"]

    def description(self, url):
        e = self.bs4(url)
        p = e.find("p", {"class": "article-full__chapo"})
        for elem in p.find_all("span"):
            elem.decompose()
        return p.text.strip()

    def date(self, url):
        e = self.bs4(url)
        return e.find("time").attrs["content"][:10]
