import requests
from bs4 import BeautifulSoup

from ..core.session import session
from ..core.website import Website


class WashingtonPost(Website):
    base_url = "https://www.washingtonpost.com/"

    article_node = ("div", {"class": "article-body"})

    def __init__(self):
        super().__init__()
        session.get(self.base_url)
        cookie_obj = requests.cookies.create_cookie(
            domain="washingtonpost.com",
            name="wp_gdpr",
            value="1|1",
        )
        session.cookies.set_cookie(cookie_obj)

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
