from ..core.website import Website


class Yomiuri(Website):
    base_url = "https://www.yomiuri.co.jp/"

    header_entries = ["title", "date", "url"]

    article_node = ("div", {"class": "p-main-contents"})
    clean_nodes = ["figure", "aside", "div"]
