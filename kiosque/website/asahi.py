from bs4 import BeautifulSoup

from ..core.website import Website


class Asahi(Website):
    base_url = "https://www.asahi.com/"

    header_entries = ["title", "date", "url"]

    article_node = ("div", {"class": "_3YqJ1"})
    clean_attributes = ["a"]

    def clean(self, article):
        article = super().clean(article)

        new_article = BeautifulSoup("<article></article>", features="lxml")

        for elem in article.find_all("p"):
            new_article.append(elem)

        return new_article
