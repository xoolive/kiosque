from ..core.website import Website


class _01Net(Website):
    base_url = "https://www.01net.com/"

    article_node = "div", {"itemprop": "articleBody"}
    clean_nodes = ["figure"]
    clean_attributes = ["h3"]
