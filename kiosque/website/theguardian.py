from ..core.website import Website


class TheGuardian(Website):
    base_url = "https://www.theguardian.com/"

    article_node = "div", {"class": "article-body-viewer-selector"}
    clean_nodes = ["figure", "div"]

    def author(self, url):
        author_node = self.bs4(url).find("a", {"rel": "author"})
        if author_node is not None:
            return author_node.text
