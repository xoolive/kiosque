"""Aviation Week website scraper.

Uses Auth0 Universal Login with OAuth 2.0 PKCE for authentication.
"""

import base64
import hashlib
import logging
import secrets
from datetime import datetime
from typing import ClassVar, cast

from bs4 import BeautifulSoup, Tag
from bs4._typing import _StrainableAttributes

from ..core.client import client
from ..core.website import Website


class AviationWeek(Website):
    base_url = "https://aviationweek.com/"
    # User login initiates OAuth flow
    login_url = "https://aviationweek.com/user/login"

    title_meta: ClassVar[_StrainableAttributes] = {"name": "title"}
    description_meta: ClassVar[_StrainableAttributes] = {"name": "description"}

    clean_nodes: ClassVar[list[str | tuple[str, _StrainableAttributes]]] = [
        ("div", {"class": ["dfp-ad", "dfp-tag"]})
    ]

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
        """Perform OAuth 2.0 with PKCE login via Auth0 Universal Login."""
        credentials = self.credentials
        assert credentials is not None

        logging.info(f"Logging in at {self.login_url}")

        # Step 1: Generate PKCE pair
        _code_verifier, code_challenge = self._generate_pkce_pair()

        # Step 2: Initiate OAuth flow with PKCE
        # GET /user/login redirects to Auth0 authorize endpoint
        auth_params = {
            "client_id": "PZ-a176tAbl1SuTbp9u25uYaC4WqpWhh",
            "redirect_uri": "https://aviationweek.com/auth0/callback",
            "response_type": "code",
            "response_mode": "query",
            "scope": "openid email profile",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        response = client.get(
            "https://login.aviationweek.com/authorize",
            params=auth_params,
            follow_redirects=True,
        )
        response.raise_for_status()

        # Step 3: Extract state from Auth0 Universal Login page
        # The page redirects to /u/login?state=...
        login_page_url = str(response.url)

        # Step 4: Parse form to get the state value
        soup = BeautifulSoup(response.content, "html.parser")
        form = soup.find("form")
        if not form:
            raise ValueError("Could not find login form in Auth0 response")

        state_input = form.find("input", {"name": "state"})
        if not state_input:
            raise ValueError("Could not find state input in login form")

        state = state_input.get("value")

        # Step 5: Submit credentials to Auth0
        # Auth0 Universal Login POSTs to the same URL
        login_data = {
            "state": state,
            "username": credentials["username"],
            "password": credentials["password"],
        }

        login_response = client.post(
            login_page_url, data=login_data, follow_redirects=True
        )
        login_response.raise_for_status()

        # Step 6: Check if login was successful
        # Auth0 should redirect to: https://aviationweek.com/auth0/callback?code=...
        final_url = str(login_response.url)
        if "code=" in final_url or "aviationweek.com" in final_url:
            # Successfully logged in - session cookies are now set
            self.__class__.connected = True
            logging.info("Successfully logged in to Aviation Week")
            return login_response

        # If we're still on login.aviationweek.com, login likely failed
        if "login.aviationweek.com" in final_url:
            raise ValueError(
                "Login failed - still on Auth0 login page. Check credentials."
            )

        return login_response

    def article(self, url):
        e = self.bs4(url)
        article = cast(Tag, e.find("article"))
        return article.find("div", {"class": "article__body"})

    def clean(self, article):
        article = super().clean(article)
        article = article.find("div")
        article.name = "article"
        return article

    def date(self, url):
        e = self.bs4(url)
        date_node = e.find("span", {"class": "article__date"})
        if date_node is None:
            return None
        date = datetime.strptime(date_node.text, "%B %d, %Y")  # noqa: DTZ007
        return f"{date:%Y-%m-%d}"

    def author(self, url):
        e = self.bs4(url)
        author = e.find("a", {"class": "author--teaser__name"})
        if author is not None:
            return author.text
