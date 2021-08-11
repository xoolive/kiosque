from ..core.website import Website


class FinancialTimes(Website):
    base_url = "https://www.ft.com/"

    article_node = "div", {"class": "article__content-body"}
    clean_nodes = ["figure", "div", "aside"]
