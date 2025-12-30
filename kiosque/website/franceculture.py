from typing import ClassVar

from ..core.website import Website


class FranceCulture(Website):
    base_url = "https://www.franceculture.fr/"
    article_node = ("div", {"class": "content-body"})

    clean_nodes: ClassVar = ["div", "figure", "aside"]

    def author(self, url):
        author = super().author(url)
        if author is not None:
            return author

        e = self.bs4(url)
        node = e.find("div", {"class": "heading-zone-title-owner"})
        if node is None:
            return None

        author = node.find("a")
        if author is None:
            return None

        return author.text  # type: ignore
