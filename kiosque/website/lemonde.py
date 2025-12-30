from typing import ClassVar

from bs4 import BeautifulSoup

from ..core.client import get_with_retry
from ..core.website import Website


class LeMonde(Website):
    base_url = "https://www.lemonde.fr/"
    login_url = "https://secure.lemonde.fr/sfuser/connexion"
    alias: ClassVar = ["lemonde"]

    clean_nodes: ClassVar = [
        "figure",  # Remove images
        ("section", {"class": "author"}),  # Author bio
        ("section", {"class": "article__reactions"}),  # Reactions section
    ]
    clean_attributes: ClassVar = ["h2"]

    @property
    def login_dict(self):
        credentials = self.credentials
        assert credentials is not None

        # Fetch login page to get CSRF token
        c = get_with_retry(self.login_url)
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")

        # Extract CSRF token from hidden input
        token_input = e.find("input", {"name": "csrf"})
        if token_input is None:
            raise ValueError("CSRF token not found on login page")
        token = token_input.attrs["value"]  # type: ignore

        return {
            "email": credentials["username"],
            "password": credentials["password"],
            "csrf": token,
            "newsletters": "[]",  # Hidden field, empty array as string
        }

    def article(self, url):
        e = self.bs4(url)
        article = e.find("article", attrs={"class": "article__content"})
        if article is None:
            article = e.find("section", attrs={"class": "article__content"})
        else:
            embedded = article.find(
                "section", attrs={"class": "article__content"}
            )
            if embedded is not None:
                article = embedded

        return article

    def clean(self, article):
        """Remove unwanted elements from Le Monde articles.

        Removes:
        - Promotional sections (newsletters, app promos)
        - "Read also" recommendation sections
        - Ad slots and comment sections
        - Author info sections
        """
        article = super().clean(article)

        # Remove sections with class containing 'inread' (newsletter/app promos)
        for elem in list(article.find_all("section")):
            classes = elem.get("class", [])
            class_str = " ".join(classes).lower()
            if "inread" in class_str or "catcher" in class_str:
                elem.decompose()

        # Remove divs with ad/paywall/comment classes
        for elem in list(article.find_all("div")):
            classes = elem.get("class", [])
            class_str = " ".join(classes).lower()
            if any(
                keyword in class_str
                for keyword in [
                    "inread",
                    "dfp",
                    "paywall",
                    "comments__blocked",
                    "catcher",
                ]
            ):
                elem.decompose()

        # Remove spans with unwanted classes
        for elem in list(article.find_all("span")):
            classes = elem.get("class", [])
            class_str = " ".join(classes).lower()
            if any(keyword in class_str for keyword in ["inread", "catcher"]):
                elem.decompose()

        # Convert h3 to blockquote (Le Monde specific styling)
        for elem in article.find_all("h3"):
            elem.name = "blockquote"
            elem.attrs.clear()

        return article
