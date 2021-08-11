from ..core.website import Website


class NBCNews(Website):
    base_url = "https://www.nbcnews.com/"

    article_node = "div", {"class": "article-body__content"}
    clean_nodes = ["div", "figure", "section"]

    def date(self, url):
        return (
            self.bs4(url)
            .find("meta", {"itemprop": "datePublished"})
            .attrs["content"][:10]
        )

    def author(self, url):
        for elem in self.bs4(url).find_all("a"):
            if "href" in elem.attrs and elem.attrs["href"].startswith(
                "https://www.nbcnews.com/author/"
            ):
                return elem.text
