import re
from pathlib import Path

import pypandoc
from bs4 import BeautifulSoup

from ..core.download import Download


class LeMonde(Download):

    base_url = "https://www.lemonde.fr/"
    login_url = "https://secure.lemonde.fr/sfuser/connexion"

    def login_dict(self):
        c = self.session.get(self.login_url)
        c.raise_for_status()

        e = BeautifulSoup(c.content, features="lxml")
        attrs = dict(name="connection[_token]")
        token = e.find("input", attrs=attrs).attrs["value"]

        return {
            "connection[mail]": self.credentials["mail"],
            "connection[password]": self.credentials["password"],
            "connection[stay_connected]": 1,
            "connection[save]": "",
            "connection[newsletters]": [],
            "connection[_token]": token,
        }

    def get_content(self, url):
        c = self.session.get(url)

        m = re.search(r"\d{4}/\d{2}/\d{2}", url)
        assert m is not None
        date = m.group().replace("/", "-")

        filename = f"{date}-{url.split('/')[-1].replace('.html', '.md')}"

        e = BeautifulSoup(c.content, features="lxml")

        # main_body = e.find("section", attrs={"class": "zone--article"})

        title = e.find("h1")
        author = e.find("a", attrs={"class": "article__author"})
        if author is None:
            author = e.find("a", attrs={"class": "article__author-link"})
        desc = e.find("p", attrs={"class": "article__desc"})

        header = f"""---
title: {title.text.strip()}
author: {author.text.strip()}
date: {date}
header: {desc.text.strip()}
---
        """

        article = e.find("article", attrs={"class": "article__content"})
        if article is None:
            article = e.find("section", attrs={"class": "article__content"})
        else:
            embedded = article.find(
                "section", attrs={"class": "article__content"}
            )
            if embedded is not None:
                article = embedded

        for x in article.find_all("section", attrs={"class": "catcher"}):
            x.decompose()
        for x in article.find_all("section", attrs={"class": "author"}):
            x.decompose()
        for x in article.find_all(
            "section", attrs={"class": "article__reactions"}
        ):
            x.decompose()
        for x in article.find_all("div", attrs={"class": "dfp__inread"}):
            x.decompose()

        for x in article.find_all("h2"):
            x.attrs.clear()
        for x in article.find_all("h3"):
            x.name = "blockquote"
            x.attrs.clear()
        for x in article.find_all("figure"):
            x.decompose()

        output = pypandoc.convert_text(article, "md", format="html")

        print(filename)
        Path(filename).write_text(f"{header}\n\n{output}")
