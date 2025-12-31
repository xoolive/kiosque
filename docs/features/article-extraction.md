# Article Extraction

Extract full-text articles from 32+ paywalled news websites.

---

## Overview

Kiosque can download complete articles from major news publications, converting them to clean Markdown format with metadata preserved.

## Basic Usage

### Command Line

```bash
# Extract to file
kiosque https://www.lemonde.fr/article.html output.md

# Print to stdout
kiosque https://www.nytimes.com/article.html -

# Use with pipes
kiosque https://www.lemonde.fr/article.html - | grep "keyword"
```

### Python API

```python
from kiosque import Website

# Extract article
url = "https://www.lemonde.fr/article.html"
website = Website.instance(url)
markdown = website.full_text(url)

# Get metadata
title = website.title(url)
author = website.author(url)
date = website.date(url)
```

---

## Output Format

Articles are extracted as Markdown with YAML frontmatter:

```markdown
---
title: Article Title
author: Author Name
date: 2025-12-31
url: https://www.example.com/article
description: Article summary
---

# Article Title

**By Author Name** · 2025-12-31

_Article summary_

---

Article content in clean Markdown format...
```

---

## Supported Sites

See [Supported Sites](../websites/supported-sites.md) for the complete list of 32+ websites.

Major publications include:

- **English**: New York Times, The Guardian, Financial Times, The Atlantic
- **French**: Le Monde, Le Figaro, Les Échos, Mediapart
- **Japanese**: Nikkei, Asahi Shimbun, Yomiuri Shimbun

---

## Authentication

Many sites require a paid subscription. Configure credentials in `~/.config/kiosque/kiosque.conf`:

```ini
[https://www.lemonde.fr/]
username = your.email@example.com
password = your_password

[https://www.nytimes.com/]
cookie_nyt_s = your_nyt_cookie_value
```

See [Authentication Guide](../websites/authentication.md) for site-specific setup.

---

## Proxy Support

Bypass geo-blocking with SOCKS or HTTP proxies:

```bash
# Command line
kiosque --proxy socks5://localhost:8765 https://www.nytimes.com/article.html output.md

# Configuration file
[proxy]
url = socks5://localhost:8765
```

**Supported formats:** `socks5://`, `socks4://`, `http://`, `https://`

See [Troubleshooting](../troubleshooting.md) for detailed proxy setup instructions.

---

## Advanced Options

### Retry Logic

Kiosque automatically retries failed requests with exponential backoff:

- **3 attempts** by default
- **2s, 4s, 8s** delays between retries
- Handles temporary network issues

### PDF Downloads

Some publications support PDF export:

```python
website = Website.instance(url)
pdf_url = website.pdf_url(url)  # Returns PDF download URL if available
```

### Custom Headers

Override HTTP headers for specific sites:

```python
from kiosque.core.client import client

client.headers.update({
    "User-Agent": "Custom User Agent",
    "Referer": "https://example.com"
})
```

---

## Troubleshooting

Common issues:

- **403 Forbidden**: Check authentication credentials
- **Geo-blocked**: Use a proxy server
- **Incomplete content**: Site may have updated their HTML structure
- **Rate limiting**: Wait and retry later

See [Troubleshooting Guide](../troubleshooting.md) for more help.

---

## Next Steps

- **[Supported Sites](../websites/supported-sites.md)** - Full list of websites
- **[Authentication](../websites/authentication.md)** - Set up site logins
- **[Contributing](../development/contributing.md)** - Add your favorite site
