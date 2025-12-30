from typing import ClassVar

from ..core.website import Website


class TheAtlantic(Website):
    base_url = "https://www.theatlantic.com/"

    author_meta: ClassVar = {"name": ["author"]}

    clean_nodes: ClassVar = ["div"]

    def article(self, url):
        e = self.bs4(url)
        for section in e.find("article").find_all("section"):
            for c in section.attrs.get("class", []):
                if "ArticleBody" in c:
                    return section
