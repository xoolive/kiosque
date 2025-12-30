from typing import ClassVar

from ..core.website import Website  # ty:ignore[unresolved-import]


class ZeroOneNet(Website):
    base_url = "https://www.01net.com/"
    article_node = "div", {"itemprop": "articleBody"}
    clean_nodes: ClassVar = ["figure"]
    clean_attributes: ClassVar = ["h3"]
