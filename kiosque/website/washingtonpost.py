import requests
from bs4 import BeautifulSoup

from ..core.client import client
from ..core.website import Website


class WashingtonPost(Website):
    base_url = "https://www.washingtonpost.com/"

    article_node = ("div", {"class": "article-body"})

    def __init__(self):
        super().__init__()
        client.get(self.base_url)
        cookie_obj = requests.cookies.create_cookie(
            domain="washingtonpost.com",
            name="wp_gdpr",
            value="1|1",
        )
        client.cookies.set_cookie(cookie_obj)

    def author(self, url):
        author = self.bs4(url).find("a", {"data-qa": "author-name"})
        if author is not None:
            return author.text

    def clean(self, article):
        article = super().clean(article)

        new_article = BeautifulSoup("<article></article>", features="lxml")

        for elem in article.find_all("p"):
            new_article.append(elem)

        return new_article
