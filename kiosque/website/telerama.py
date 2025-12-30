from typing import ClassVar

from ..core.website import Website


class Telerama(Website):
    base_url = "https://www.telerama.fr/"

    article_node = "article"
    clean_nodes: ClassVar = ["section", "div"]
