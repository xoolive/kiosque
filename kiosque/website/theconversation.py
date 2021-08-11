from ..core.website import Website


class TheConversation(Website):
    base_url = "https://theconversation.com/"

    article_node = "div", {"itemprop": "articleBody"}
    clean_nodes = ["figure"]

    def author(self, url):
        author_node = self.bs4(url).find("meta", {"name": "author"})
        if author_node is not None:
            return author_node.attrs["content"].strip()
