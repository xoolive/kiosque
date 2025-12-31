# Adding New Websites

This guide explains how to contribute support for new websites to Kiosque.

## Quick Start

Adding a new website typically involves:

1. Creating a new Python file in `kiosque/website/`
2. Implementing a class that extends `Website`
3. Defining the article extraction logic
4. (Optional) Adding authentication if the site is paywalled
5. Testing your implementation
6. Submitting a pull request

## Step-by-Step Guide

For a complete tutorial on adding new website support, see the [Contributing Guide](../development/contributing.md).

The contributing guide includes:

- Prerequisites and development setup
- Website scraper implementation patterns
- Authentication methods (simple, CSRF tokens, cookies)
- Testing procedures
- Code style guidelines
- Pull request submission process

## Quick Example

Here's a minimal example for a public website:

```python
from typing import ClassVar
from ..core.website import Website

class ExampleNews(Website):
    base_url = "https://example.com/"

    clean_nodes: ClassVar = ["figure", "aside"]

    def article(self, url):
        soup = self.bs4(url)
        return soup.find("article", class_="main-content")
```

## Common Patterns

### With Authentication

```python
class PaywalledNews(Website):
    base_url = "https://paywalled.com/"
    login_url = "https://paywalled.com/login"

    @property
    def login_dict(self):
        credentials = self.credentials
        assert credentials is not None
        return {
            "email": credentials["username"],
            "password": credentials["password"],
        }

    def article(self, url):
        soup = self.bs4(url)
        return soup.find("div", class_="article-body")
```

### With Custom Cleanup

```python
def clean(self, article):
    article = super().clean(article)

    # Remove empty paragraphs
    for p in article.find_all("p"):
        if not p.get_text(strip=True):
            p.decompose()

    return article
```

## File Naming

- Use lowercase, no spaces: `lemonde.py`, `nytimes.py`
- Name after the publication, not the domain
- Keep it simple and recognizable

## Testing Checklist

Before submitting:

- [ ] Article extraction works on multiple articles
- [ ] Authentication works (if applicable)
- [ ] Code passes `ruff check` and `ruff format`
- [ ] Tests pass: `uv run pytest -m "not login"`
- [ ] Website added to `websites.md`

## Resources

- **[Full Contributing Guide](../development/contributing.md)** - Complete implementation tutorial
- **[Architecture Guide](../development/architecture.md)** - System design and patterns
- **Existing Implementations** - Check `kiosque/website/` for 30+ examples

## Getting Help

- Open a [GitHub Issue](https://github.com/xoolive/kiosque/issues) with the `website-support` label
- Check existing website implementations in `kiosque/website/` for patterns
- See [Supported Sites](supported-sites.md) for the list of current implementations

## Thank You!

Your contributions help make journalism more accessible. Thank you for supporting Kiosque!
