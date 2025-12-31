# Contributing to Kiosque

Thank you for your interest in contributing to Kiosque! This guide will help you add support for new websites.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Adding a New Website](#adding-a-new-website)
3. [Website Scraper Implementation Guide](#website-scraper-implementation-guide)
4. [Testing Your Implementation](#testing-your-implementation)
5. [Code Style Guidelines](#code-style-guidelines)
6. [Submitting a Pull Request](#submitting-a-pull-request)

## Getting Started

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Active subscription to the website you want to add (for testing authentication)
- Basic understanding of HTML/CSS selectors

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/kiosque.git
cd kiosque

# Install dependencies with development tools
uv sync --dev

# Run the application
uv run kiosque

# Run tests (excluding login tests that require credentials)
uv run pytest -m "not login"

# Run all tests including login tests (requires credentials in kiosque.conf)
uv run pytest

# Run only login tests
uv run pytest -m "login"

# Format and lint code
uv run ruff format .
uv run ruff check .
```

### Test Configuration

**Login Tests:** Tests in `tests/test_login.py` require real credentials and are marked with `@pytest.mark.login`. These tests:

- Make real HTTP requests to websites
- Require credentials configured in `~/.config/kiosque/kiosque.conf`
- Are automatically excluded in CI/CD to protect credentials
- Should be run locally before submitting login-related changes

**Running Tests:**

```bash
# CI-safe tests only (no credentials required)
uv run pytest -m "not login"

# All tests including login (requires credentials)
uv run pytest

# Specific login test
uv run pytest tests/test_login.py::test_website_login -k "lemonde"
```

## Adding a New Website

### Step 1: Analyze the Website Structure

Before writing code, inspect the target website:

1. **Find the article container:**
   - Open an article in your browser
   - Right-click the main article text → "Inspect Element"
   - Identify the HTML element containing the article (usually `<article>`, `<div class="article">`, etc.)
   - Note the CSS class or ID

2. **Identify elements to remove:**
   - Look for elements to exclude: ads, "Read more" buttons, related articles, social media buttons
   - Note their HTML tags and classes

3. **Check authentication (if paywalled):**
   - Open browser DevTools → Network tab
   - Log in to the website
   - Inspect the login request:
     - URL (usually ends in `/login`, `/signin`, `/auth`)
     - Request method (POST)
     - Form data (username field, password field, CSRF tokens, etc.)

### Step 2: Create the Website Module

Create a new file in `kiosque/website/` named after the publication:

**File naming convention:**

- Lowercase, no spaces
- Use publication name: `lemonde.py`, `nytimes.py`, `washingtonpost.py`

### Step 3: Implement the Website Class

Here's a complete template with explanations:

```python
from typing import ClassVar
from ..core.website import Website

class YourWebsiteName(Website):
    # REQUIRED: Base URL of the website (must end with /)
    base_url = "https://example.com/"

    # OPTIONAL: Login URL (only if authentication required)
    login_url = "https://example.com/login"

    # OPTIONAL: Short aliases for CLI usage
    alias: ClassVar = ["example", "ex"]

    # OPTIONAL: HTML elements to remove (list of tags or (tag, attributes) tuples)
    clean_nodes: ClassVar = [
        "figure",  # Remove all <figure> tags
        "aside",   # Remove all <aside> tags
        ("div", {"class": "advertisement"}),  # Remove specific divs
        ("section", {"class": ["social", "related"]}),  # Multiple classes
    ]

    # OPTIONAL: Elements to strip all attributes from
    clean_attributes: ClassVar = ["h2", "blockquote"]

    # REQUIRED: Extract article content from page
    def article(self, url):
        """Return the BeautifulSoup element containing article text."""
        soup = self.bs4(url)  # Fetch and parse HTML

        # Find the main article container
        # Option 1: Single element
        article = soup.find("article", class_="main-content")

        # Option 2: Multiple possible selectors
        if article is None:
            article = soup.find("div", class_="article-body")

        # Option 3: Complex selection
        # article = soup.find("div", {"id": "content"}).find("article")

        return article

    # OPTIONAL: Custom login logic (only if authentication required)
    @property
    def login_dict(self):
        """Return form data for login POST request."""
        credentials = self.credentials
        assert credentials is not None

        # Simple case: just username and password
        return {
            "username": credentials["username"],
            "password": credentials["password"],
        }

        # Complex case: CSRF token from login page
        # response = get_with_retry(self.login_url)
        # soup = BeautifulSoup(response.content, features="lxml")
        # token = soup.find("input", {"name": "csrf_token"})["value"]
        # return {
        #     "email": credentials["username"],
        #     "password": credentials["password"],
        #     "csrf_token": token,
        # }

    # OPTIONAL: Additional cleanup (if declarative cleanup isn't enough)
    def clean(self, article):
        """Perform custom cleanup transformations."""
        # Always call parent implementation first
        article = super().clean(article)

        # Example: Convert <h3> tags to <blockquote>
        for elem in article.find_all("h3"):
            elem.name = "blockquote"
            elem.attrs.clear()

        # Example: Remove empty paragraphs
        for p in article.find_all("p"):
            if not p.get_text(strip=True):
                p.decompose()

        return article
```

## Website Scraper Implementation Guide

### Minimal Implementation (No Authentication)

For public websites like The Guardian:

```python
from typing import ClassVar
from ..core.website import Website

class TheGuardian(Website):
    base_url = "https://www.theguardian.com/"

    clean_nodes: ClassVar = ["figure", "aside"]

    def article(self, url):
        soup = self.bs4(url)
        return soup.find("div", class_="article-body-viewer-selector")
```

### Simple Authentication

For websites with straightforward login forms:

```python
from typing import ClassVar
from ..core.website import Website

class SimpleNews(Website):
    base_url = "https://simplenews.com/"
    login_url = "https://simplenews.com/auth/login"

    @property
    def login_dict(self):
        return {
            "email": self.credentials["username"],
            "password": self.credentials["password"],
        }

    def article(self, url):
        soup = self.bs4(url)
        return soup.find("article", class_="content")
```

### Complex Authentication (CSRF Token)

For websites that require CSRF tokens or multi-step login:

```python
from typing import ClassVar
from bs4 import BeautifulSoup
from ..core.client import get_with_retry
from ..core.website import Website

class ComplexNews(Website):
    base_url = "https://complexnews.com/"
    login_url = "https://secure.complexnews.com/login"

    @property
    def login_dict(self):
        credentials = self.credentials
        assert credentials is not None

        # Fetch login page to get CSRF token
        response = get_with_retry(self.login_url)
        soup = BeautifulSoup(response.content, features="lxml")

        # Extract token from hidden input
        token_input = soup.find("input", {"name": "_token"})
        token = token_input["value"]

        return {
            "username": credentials["username"],
            "password": credentials["password"],
            "_token": token,
            "remember_me": 1,
        }

    def article(self, url):
        soup = self.bs4(url)
        return soup.find("div", class_="article-content")
```

### Advanced Cleanup

For websites with complex HTML that needs transformation:

```python
def clean(self, article):
    """Example: Transform Guardian-style article HTML."""
    article = super().clean(article)

    # Convert styled headings to proper semantic headings
    for elem in article.find_all("p", class_="heading"):
        elem.name = "h3"
        elem.attrs.clear()

    # Remove empty paragraphs
    for p in article.find_all("p"):
        if not p.get_text(strip=True):
            p.decompose()

    # Unwrap unnecessary div wrappers
    for div in article.find_all("div", class_="paragraph-wrapper"):
        div.unwrap()

    return article
```

## Testing Your Implementation

### 1. Manual Testing

```bash
# Test article download (public website)
uv run kiosque https://example.com/article test.md

# Test with verbose logging (to see login flow)
uv run kiosque -v https://paywalled.com/article test.md
```

### 2. Configure Credentials (for paywalled sites)

Edit `~/.config/kiosque/kiosque.conf`:

```ini
[https://example.com/]
username = your.email@example.com
password = your_password
```

### 3. Write Tests

Create or update `tests/test_login.py` to add your website:

```python
# Add your website credentials to kiosque.conf, then:
# The parameterized test will automatically test your login flow

# If login is broken or website structure changed:
KNOWN_BROKEN_LOGINS = {
    # ... existing entries ...
    "https://yourwebsite.com/",  # Brief reason why broken
}
```

### 4. Run Tests

```bash
# Run all tests
uv run pytest

# Run specific test for your website (if configured)
uv run pytest tests/test_login.py -k "yourwebsite"

# Run with output to debug
uv run pytest tests/test_login.py -v -s
```

## Code Style Guidelines

### Formatting and Linting

**Always run before committing:**

```bash
# Format code
uv run ruff format .

# Check for issues
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check --fix .
```

### Type Hints

Use modern type syntax (Python 3.12+):

```python
# Good ✓
from typing import ClassVar

clean_nodes: ClassVar = ["figure", "aside"]

def article(self, url: str) -> BeautifulSoup | None:
    ...

# Bad ✗
from typing import Optional, List, Type

clean_nodes = ["figure", "aside"]  # Missing ClassVar

def article(self, url):  # Missing type hints
    ...
```

### Import Organization

```python
# Standard library
from typing import ClassVar

# Third-party
from bs4 import BeautifulSoup

# Local imports (relative)
from ..core.client import get_with_retry
from ..core.website import Website
```

### Class Variable Annotations

All mutable class attributes **must** be annotated with `ClassVar`:

```python
# Good ✓
clean_nodes: ClassVar = ["figure"]
clean_attributes: ClassVar = ["h2"]
alias: ClassVar = ["example"]

# Bad ✗
clean_nodes = ["figure"]  # Missing ClassVar annotation
```

### Docstrings

Add docstrings for complex methods:

```python
def article(self, url):
    """Extract main article content from the page.

    Args:
        url: Full URL of the article

    Returns:
        BeautifulSoup element containing article text, or None if not found
    """
    ...
```

## Submitting a Pull Request

### Before Submitting

1. **Test your implementation:**

   ```bash
   # Download multiple articles
   uv run kiosque https://example.com/article1 test1.md
   uv run kiosque https://example.com/article2 test2.md

   # Verify Markdown output is clean and complete
   bat test1.md  # or open in your editor
   ```

2. **Run all checks:**

   ```bash
   uv run ruff format .
   uv run ruff check .
   uv run pytest
   ```

3. **Update documentation:**
   - Add website to [Supported Sites](../websites/supported-sites.md) in the appropriate language section
   - Indicate if authentication is supported (☑️)

### PR Guidelines

1. **Branch naming:** `add-website-<name>` (e.g., `add-website-nytimes`)

2. **Commit message format:**

   ```
   Add support for Example News website

   - Implements article extraction for example.com
   - Adds authentication support with CSRF token handling
   - Includes test for login flow
   ```

3. **PR description should include:**
   - Brief description of the website
   - Whether authentication is supported
   - Any special considerations (e.g., "Login requires solving captcha manually")
   - Example article URLs you tested

4. **Don't commit credentials:**
   - `kiosque.conf` is in `.gitignore` - never commit it
   - Don't include passwords or API tokens in code or PR

### PR Template

```markdown
## Description

Adds support for Example News (https://example.com/)

## Authentication

- [x] Requires subscription
- [x] Login flow implemented
- [ ] Publicly accessible

## Testing

Tested with the following articles:

- https://example.com/article1
- https://example.com/article2

## Checklist

- [x] Code formatted with `ruff format`
- [x] No linting errors (`ruff check`)
- [x] Tests pass (`pytest`)
- [x] Added website to [Supported Sites](../websites/supported-sites.md)
- [x] Tested article extraction manually
```

## Common Patterns and Gotchas

### Finding Article Elements

```python
# Try multiple selectors
def article(self, url):
    soup = self.bs4(url)

    # Try primary selector
    article = soup.find("article", class_="main")

    # Fallback to alternative
    if article is None:
        article = soup.find("div", id="content")

    return article
```

### Handling CSRF Tokens

```python
from bs4 import BeautifulSoup
from ..core.client import get_with_retry

@property
def login_dict(self):
    # Fetch login page
    response = get_with_retry(self.login_url)
    soup = BeautifulSoup(response.content, features="lxml")

    # Find token (adapt selector to website)
    token = soup.find("input", {"name": "csrf"})["value"]

    return {
        "username": self.credentials["username"],
        "password": self.credentials["password"],
        "csrf": token,
    }
```

### Removing Unwanted Elements

```python
# Declarative (preferred for simple cases)
clean_nodes: ClassVar = [
    "figure",
    ("div", {"class": "ad"}),
]

# Imperative (for complex logic)
def clean(self, article):
    article = super().clean(article)

    # Remove by complex criteria
    for elem in article.find_all("div"):
        if "ad" in elem.get("class", []):
            elem.decompose()

    return article
```

### Debugging Tips

```python
# Add verbose logging
import logging

def article(self, url):
    soup = self.bs4(url)
    article = soup.find("article")

    if article is None:
        logging.error(f"Could not find article in {url}")
        logging.debug(f"Page HTML: {soup.prettify()[:500]}")

    return article
```

## Getting Help

- **Issues:** Open a GitHub issue with the `website-support` label
- **Questions:** Start a discussion in GitHub Discussions
- **Documentation:** See [Architecture](architecture.md) for system design
- **Examples:** Check `kiosque/website/` for 30+ real implementations

## Thank You!

Your contributions help make journalism more accessible. Thank you for supporting Kiosque! 🎉
