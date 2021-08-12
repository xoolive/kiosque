from ..core.website import Website


class NewYorker(Website):
    base_url = "https://www.newyorker.com/"

    article_node = "div", {"data-attribute-verso-pattern": "article-body"}
    clean_nodes = ["figure"]
    clean_attributes = ["blockquote", "h1"]

    def author(self, url):
        e = self.bs4(url)
        author_node = e.find("p", {"itemprop": "author"}).find("a")
        if author_node is not None:
            return author_node.text

    def clean(self, article):
        article = super().clean(article)

        for elem in article.find_all("div"):
            if article.find("blockquote") or article.find("p"):
                elem.name = "quote"
                elem.attrs.clear()
            else:
                elem.decompose()

        for elem in article.find_all("a"):
            if "class" in elem.attrs:
                del elem.attrs["class"]

        return article
