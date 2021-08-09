from ..core.website import Website


class Nikkei(Website):
    base_url = "https://asia.nikkei.com/"

    article_node = ("div", {"class": "ezrichtext-field"})
    clean_nodes = ["div"]
