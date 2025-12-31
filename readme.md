# kiosque

A unified tool for news article extraction and bookmark management.

## What is Kiosque?

Kiosque combines three essential capabilities:

1. **Article Extractor (CLI/API)** - Download full-text articles from several paywalled news websites as Markdown
2. **Bookmark Manager (TUI)** - Browse and manage bookmarks from Raindrop.io and GitHub Stars in a beautiful terminal interface
3. **Content Aggregator** - Unified tabbed interface for multiple content sources with smart context-aware actions

## Quick Start

```bash
# Launch TUI (Terminal User Interface) - default
kiosque

# Extract article to file
kiosque https://www.lemonde.fr/article output.md

# Print to stdout
kiosque https://www.nytimes.com/article - | bat - -l md
```

## Installation

```bash
# From PyPI
pip install kiosque

# Or with uv (recommended)
uv tool install kiosque
```

**Requirements:** Python 3.12+, pandoc

## Core Features

### 📰 Article Extraction

- **32+ News Websites** - Le Monde, NYT, Guardian, Mediapart, and more
- **Authentication** - Login support for paywalled sites
- **Markdown Output** - Clean, readable format with metadata
- **Proxy Support** - Access geo-blocked websites via SOCKS/HTTP proxies

### 🔖 Bookmark Management

- **Raindrop.io Integration** - Browse, preview, archive, delete, edit tags
- **GitHub Stars** - Explore starred repos, preview READMEs, unstar
- **Unified Search** - Filter by title, URL, tags, topics across all sources
- **Beautiful Previews** - Markdown rendering with syntax highlighting

### 🚀 Content Aggregation

- **Tabbed Interface** - Switch between Raindrop and GitHub (`1`/`2`)
- **Progressive Loading** - Non-blocking, fast performance
- **Smart Actions** - Context-aware keybindings (e.g., star GitHub repos from Raindrop)
- **Live Counts** - `Kiosque (42) · Raindrop (30) · GitHub (12)`

## Configuration

Create `~/.config/kiosque/kiosque.conf`:

```ini
# Website authentication
[https://www.lemonde.fr/]
username = your.email@example.com
password = your_password

[https://www.nytimes.com/]
cookie_nyt_s = your_nyt_cookie_value

# Raindrop.io integration
[raindrop.io]
token = your_raindrop_api_token

# GitHub Stars integration
[github]
token = ghp_your_github_personal_access_token

# Proxy for geo-blocked sites (optional)
[proxy]
url = socks5://localhost:1080
```

## Python API

```python
from kiosque import Website

# Extract article as Markdown
url = "https://www.lemonde.fr/article"
markdown = Website.instance(url).full_text(url)

# Save to file
Website.instance(url).save(url, "article.md")
```

## Documentation

📚 **Full documentation:** https://www.xoolive.org/kiosque

- [Installation](https://www.xoolive.org/kiosque/getting-started/installation/) - Detailed installation guide
- [Configuration](https://www.xoolive.org/kiosque/getting-started/configuration/) - Authentication setup for all sites
- [TUI Guide](https://www.xoolive.org/kiosque/features/tui-guide/) - Complete terminal interface reference
- [Supported Sites](https://www.xoolive.org/kiosque/websites/supported-sites/) - Full list of 32+ websites
- [Authentication](https://www.xoolive.org/kiosque/websites/authentication/) - Site-specific login instructions
- [Adding Sites](https://www.xoolive.org/kiosque/websites/adding-sites/) - Contributing new website support
- [Troubleshooting](https://www.xoolive.org/kiosque/troubleshooting/) - Common issues and solutions

## TUI Keybindings

| Key                     | Action                       |
| ----------------------- | ---------------------------- |
| `↑` or `k` / `↓` or `j` | Navigate entries             |
| `1` / `2`               | Switch tabs                  |
| `/`                     | Search                       |
| `Space`                 | Preview article/README       |
| `Enter` / `o`           | Open in browser              |
| `t`                     | Edit tags (Raindrop)         |
| `e`                     | Archive (Raindrop)           |
| `d`                     | Delete (Raindrop)            |
| `u`                     | Unstar (GitHub)              |
| `s`                     | Star on GitHub (GitHub URLs) |
| `r`                     | Refresh                      |
| `q`                     | Quit                         |

## Contributing

Contributions welcome! See the [Contributing Guide](https://www.xoolive.org/kiosque/development/contributing/) for:

- How to add support for new websites
- Code style and testing guidelines
- Architecture overview

## License

MIT
