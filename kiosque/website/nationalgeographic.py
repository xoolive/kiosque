from datetime import datetime, timezone

from ..core.website import Website


class NationalGeographic(Website):
    base_url = "https://www.nationalgeographic.com/"

    article_node = "section", {"class": "Article__Content"}

    def article(self, url):
        article = super().article(url)
        return article.find("div")

    def author(self, url):
        author = self.bs4(url).find("span", {"class": "Byline__Author"})
        if author is not None:
            return author.text

    def date(self, url):
        date_node = self.bs4(url).find(
            "div", {"class": "Byline__Meta--publishDate"}
        )

        if date_node is None:
            return None
        date = datetime.strptime(
            " ".join(date_node.text.split()[1:]), "%B %d, %Y"
        ).replace(tzinfo=timezone.utc)
        return f"{date:%Y-%m-%d}"
