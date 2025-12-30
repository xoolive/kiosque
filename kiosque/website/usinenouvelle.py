"""L'Usine Nouvelle website scraper.

Uses Keycloak OAuth 2.0 with PKCE for authentication via Infopro Digital SSO.
"""

import base64
import hashlib
import logging
import re
import secrets
from typing import ClassVar

from bs4 import BeautifulSoup

from ..core.client import client
from ..core.website import Website


class UsineNouvelle(Website):
    base_url = "https://www.usinenouvelle.com/"
    # Keycloak SSO endpoint (Infopro Digital)
    login_url = "https://auth-industrie.infopro-digital.com/realms/industrie/protocol/openid-connect/auth"

    date_meta: ClassVar = {"name": ["date.modified"]}

    article_node = ("div", {"class": "epAtcBody"})
    clean_nodes: ClassVar = ["section"]

    def _generate_pkce_pair(self):
        """Generate PKCE code_verifier and code_challenge for OAuth 2.0."""
        # Generate random code verifier (43-128 characters, base64url encoded)
        code_verifier = (
            base64.urlsafe_b64encode(secrets.token_bytes(32))
            .decode("utf-8")
            .rstrip("=")
        )

        # Create code challenge: BASE64URL(SHA256(code_verifier))
        challenge_bytes = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        code_challenge = (
            base64.urlsafe_b64encode(challenge_bytes)
            .decode("utf-8")
            .rstrip("=")
        )

        return code_verifier, code_challenge

    def login(self):
        """Perform OAuth 2.0 with PKCE login via Keycloak SSO."""
        credentials = self.credentials
        assert credentials is not None

        logging.info(f"Logging in at {self.login_url}")

        # Step 1: Generate PKCE pair
        _code_verifier, code_challenge = self._generate_pkce_pair()

        # Step 2: Initiate OAuth flow with PKCE
        auth_params = {
            "client_id": "un-front",
            "redirect_uri": "https://www.usinenouvelle.com/",
            "response_type": "code",
            "scope": "openid",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        response = client.get(self.login_url, params=auth_params)
        response.raise_for_status()

        # Step 3: Extract login action URL from Keycloak's React config
        # The page contains a kcContext object with loginAction URL
        login_action_match = re.search(
            r'"loginAction":\s*"([^"]+)"', response.text
        )

        if not login_action_match:
            raise ValueError("Could not find loginAction in Keycloak response")

        login_action_url = login_action_match.group(1).replace("\\/", "/")

        # Step 4: Submit credentials to Keycloak
        login_data = {
            "username": credentials["username"],
            "password": credentials["password"],
        }

        login_response = client.post(
            login_action_url, data=login_data, follow_redirects=True
        )
        login_response.raise_for_status()

        # Step 5: Extract authorization code from redirect
        # Keycloak should redirect to: https://www.usinenouvelle.com/?code=...
        if "code=" in str(login_response.url):
            # Successfully logged in - the code is in the URL
            # The session cookies are now set
            self.__class__.connected = True
            logging.info("Successfully logged in to L'Usine Nouvelle")
            return login_response

        # Check for login errors
        if (
            "error" in response.text.lower()
            or "invalid" in response.text.lower()
        ):
            raise ValueError(
                "Login failed - check credentials. "
                "Response may contain error message."
            )

        self.__class__.connected = True
        return login_response

    def description(self, url):
        e = self.bs4(url)
        return e.find("div", {"class": "epArticleChapo"}).text.strip()

    def author(self, url):
        author = super().author(url)
        if author is not None:
            return author

        e = self.bs4(url)
        return e.find(
            "span", {"class": "epMetaData__content__infos-name"}
        ).text.strip()

    def clean(self, article):
        article = super().clean(article)

        for elem in article.find_all("span", {"class": "interTitre"}):
            elem.attrs.clear()
            elem.name = "h2"

        for elem in article.find_all("a", {"class": "lien-contextuel"}):
            elem.attrs.clear()
            elem.name = "span"

        new_article = BeautifulSoup("<article></article>", features="lxml")

        for elem in article.find_all("p"):
            new_article.append(elem)

        return new_article
