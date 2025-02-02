from ..core.website import Website


class Rugbyrama(Website):
    base_url = "https://www.rugbyrama.fr/"

    article_node = ("div", {"class": "article-full__body-content"})
    clean_nodes = ["div"]
    clean_attributes = ["h2"]

    def description(self, url):
        e = self.bs4(url)
        p = e.find("p", {"class": "article-full__chapo"})
        for elem in p.find_all("span"):
            elem.decompose()
        return p.text.strip()

    def date(self, url):
        e = self.bs4(url)
        return e.find("time").attrs["content"][:10]

    def author(self, url: str):
        e = self.bs4(url)
        author = e.find("a", {"class": "author-link"})
        if author:
            return author.text
        return ""
