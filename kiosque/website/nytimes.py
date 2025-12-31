"""New York Times website scraper.

Authentication uses cookie-based auth due to NYT's anti-bot protection.

To authenticate:
1. Log in to nytimes.com in your browser
2. Open DevTools (F12) > Application/Storage > Cookies
3. Find the 'NYT-S' cookie value
4. Add to your config file:

[https://www.nytimes.com]
cookie_nyt_s = your_cookie_value_here

The cookie typically lasts for several months.
"""

import logging

from bs4 import BeautifulSoup

from ..core.client import client
from ..core.website import Website


class NewYorkTimes(Website):
    base_url = "https://www.nytimes.com/"
    login_url = "https://myaccount.nytimes.com/auth/login"

    article_node = ("section", {"name": "articleBody"})

    def login(self):
        """Authenticate with NYT using cookie-based authentication.

        NYT has strong anti-bot protection that blocks automated browsers,
        so we use manual cookie extraction instead.

        Returns None on success, logs warning if no credentials found.
        """
        credentials = self.credentials
        if credentials is None:
            return None

        # Use pre-extracted NYT-S cookie
        cookie_value = credentials.get("cookie_nyt_s")
        if cookie_value:
            logging.info("Using NYT-S cookie for authentication")
            client.cookies.set("NYT-S", cookie_value, domain=".nytimes.com")
            self.__class__.connected = True
            return None

        # No cookie found - provide helpful instructions
        logging.warning("=" * 60)
        logging.warning("NYT authentication requires manual cookie extraction")
        logging.warning("=" * 60)
        logging.warning("1. Log in to nytimes.com in your browser")
        logging.warning(
            "2. Open DevTools (F12) > Application/Storage > Cookies"
        )
        logging.warning("3. Find the 'NYT-S' cookie and copy its value")
        logging.warning("4. Add to ~/.config/kiosque/kiosque.conf:")
        logging.warning("")
        logging.warning("   [https://www.nytimes.com]")
        logging.warning("   cookie_nyt_s = <paste_cookie_value_here>")
        logging.warning("")
        logging.warning("For detailed instructions, see: NYT_COOKIE_SETUP.md")
        logging.warning("=" * 60)

        return None

    def author(self, url: str):
        e = self.bs4(url)
        node = e.find("meta", {"name": "byl"})
        if node is None:
            return None
        date = node.attrs.get("content", None)
        if date is None:
            return None
        return date[3:]

    def clean(self, article):
        article = super().clean(article)

        # Remove paywall/subscription messages
        for elem in list(article.find_all("p")):
            text = elem.get_text().strip()
            # Remove common paywall phrases
            if any(
                phrase in text
                for phrase in [
                    "We are having trouble retrieving",
                    "Please enable JavaScript",
                    "Thank you for your patience while we verify",
                    "Already a subscriber",
                    "Want all of The Times",
                    "Log in",
                    "Subscribe",
                ]
            ):
                elem.decompose()

        # Remove divs with subscription/paywall classes
        for elem in list(article.find_all("div")):
            classes = elem.get("class", [])
            class_str = " ".join(classes).lower()
            if any(
                keyword in class_str
                for keyword in [
                    "paywall",
                    "subscription",
                    "opttrunc",
                    "meter",
                    "gate",
                ]
            ):
                elem.decompose()

        # Clean up link attributes, keeping only href
        for elem in article.find_all("a"):
            href = elem.get("href")
            elem.attrs.clear()
            if href:
                elem.attrs["href"] = href

        new_article = BeautifulSoup("<article></article>", features="lxml")

        for elem in article.find_all("p"):
            new_article.append(elem)

        return new_article
