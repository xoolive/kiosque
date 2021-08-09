from ..core.website import Website


class Mediapart(Website):
    base_url = "https://www.mediapart.fr/"
    login_url = "https://www.mediapart.fr/login_check"

    author_meta = {"name": ["author"]}

    clean_nodes = ["div"]

    @property
    def login_dict(self):
        credentials = self.credentials
        assert credentials is not None

        return dict(
            name=credentials["username"],
            password=credentials["password"],
            op="Se+connecter",
        )

    def article(self, url):
        e = self.bs4(url)
        article = e.find("div", {"class": "content-article"})

        # if not logged in
        embedded = article.find("div", {"class": "content-article"})
        if embedded is not None:
            article = embedded

        # if logged in
        embedded = article.find("div", {"class": "page-pane"})
        if embedded is not None:
            article = embedded

        return article
