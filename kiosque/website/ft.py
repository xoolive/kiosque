from typing import ClassVar

from ..core.website import Website


class FinancialTimes(Website):
    base_url = "https://www.ft.com/"
    article_node = "div", {"class": "article__content-body"}
    clean_nodes: ClassVar = ["figure", "div", "aside"]
