from bs4 import BeautifulSoup

from ..core.website import Website


class NewYorkTimes(Website):
    base_url = "https://www.nytimes.com/"

    article_node = ("section", {"name": "articleBody"})

    def author(self, url: str):
        e = self.bs4(url)
        node = e.find("meta", {"name": "byl"})
        if node is None:
            return None
        date = node.attrs.get("content", None)
        if date is None:
            return None
        return date[3:]

    def clean(self, article):
        article = super().clean(article)

        for elem in article.find_all("a"):
            if "class" in elem.attrs:
                del elem.attrs["class"]

        new_article = BeautifulSoup("<article></article>")

        for elem in article.find_all("p"):
            new_article.append(elem)

        return new_article
