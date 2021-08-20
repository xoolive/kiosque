from ..core.website import Website


class LATimes(Website):
    base_url = "https://www.latimes.com/"

    article_node = "div", {"class": "rich-text-body"}
    clean_attributes = ["span"]
    clean_nodes = ["div"]

    def author(self, url):
        e = self.bs4(url)
        return e.find("div", {"class": "author-name"}).find("a").text

    def clean(self, article):
        article = super().clean(article)

        for elem in article.find_all("a"):
            if "class" in elem.attrs:
                del elem.attrs["class"]

        return article
