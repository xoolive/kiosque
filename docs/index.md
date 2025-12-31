# Kiosque

**A unified tool for news article extraction and bookmark management.**

---

## What is Kiosque?

Kiosque is three tools in one:

1. **Article Extractor (CLI/API)** - Download full-text articles from paywalled news websites as Markdown
2. **Bookmark Manager (TUI)** - Browse and manage bookmarks from Raindrop.io and GitHub Stars in a beautiful terminal interface
3. **Content Aggregator** - Unified tabbed interface for multiple content sources with smart context-aware actions

---

## Quick Start

### Installation

```bash
# Install with pip
pip install kiosque

# Or with uv (recommended)
uv tool install kiosque
```

**Requirements:** Python 3.12+, pandoc

See [Installation Guide](getting-started/installation.md) for detailed instructions.

### Basic Usage

```bash
# Launch TUI (default when run without arguments)
kiosque

# Extract article to Markdown
kiosque https://www.lemonde.fr/article output.md

# Print to stdout (pipe to your pager)
kiosque https://www.nytimes.com/article - | bat - -l md

# Verbose mode (shows login & download progress)
kiosque -v https://url.com/article output.md
```

### Python API

```python
from kiosque import Website

# Extract article text as Markdown
url = "https://www.lemonde.fr/article"
markdown_text = Website.instance(url).full_text(url)

# Save to file
Website.instance(url).save(url, "article.md")
```

---

## Core Features

### 📰 Article Extraction

- **Many News Websites** - Support for several major publications across English and French language newspapers
- **Authentication** - Login support for paywalled sites with valid subscription
- **Markdown Output** - Clean, readable format with metadata preservation
- **Proxy Support** - Access geo-blocked websites via SOCKS/HTTP proxies
- **PDF Download** - Get latest issues from select publications (e.g., Le Monde Diplomatique)

### 🔖 Bookmark Management (TUI)

- **Raindrop.io Integration** - Browse, preview, archive, delete, and edit tags on bookmarks
- **GitHub Stars** - Explore starred repositories, preview READMEs, and unstar
- **Tag Editing** - Update tags inline with smart parsing (space/comma separated)
- **Cross-Tab Actions** - Star GitHub repos directly from Raindrop bookmarks
- **Unified Search** - Filter by title, URL, tags, and topics across all sources (300ms debounced)
- **Beautiful Previews** - Markdown rendering with syntax highlighting

### 🚀 Content Aggregation

- **Tabbed Interface** - Seamlessly switch between Raindrop and GitHub (press `1`/`2`)
- **Progressive Loading** - Non-blocking load (Raindrop first, GitHub 100ms later)
- **Smart Actions** - Context-aware keybindings (e.g., 's' to star GitHub repos)
- **Live Counts** - Window title shows: `Kiosque (42) · Raindrop (30) · GitHub (12)`

---

## TUI Quick Reference

### Navigation

| Key                   | Action                              |
| --------------------- | ----------------------------------- |
| `↑` / `↓` / `j` / `k` | Navigate entries                    |
| `Ctrl+d` / `Ctrl+u`   | Scroll down/up by 5 entries         |
| `g` / `G`             | Jump to top/bottom                  |
| `/`                   | Search/filter entries               |
| `1` / `2`             | Switch between Raindrop/GitHub tabs |

### Actions

| Key     | Action                                          |
| ------- | ----------------------------------------------- |
| `Space` | Preview article/README in modal                 |
| `Enter` | Open in browser                                 |
| `c`     | Copy URL to clipboard                           |
| `d`     | Delete bookmark (Raindrop)                      |
| `e`     | Archive bookmark (Raindrop)                     |
| `t`     | Edit tags (Raindrop)                            |
| `u`     | Unstar repository (GitHub)                      |
| `s`     | Star on GitHub (Raindrop tab, GitHub URLs only) |
| `r`     | Refresh current tab                             |
| `q`     | Quit application                                |

See [TUI Guide](features/tui-guide.md) for complete documentation.

---

## Configuration

Kiosque uses a simple INI configuration file for authentication:

```ini
# ~/.config/kiosque/kiosque.conf

# Website credentials
[https://www.lemonde.fr/]
username = your.email@example.com
password = your_password

# API integrations
[raindrop.io]
token = your_raindrop_api_token

[github]
token = ghp_your_github_personal_access_token
```

See [Configuration Guide](getting-started/configuration.md) for complete setup instructions.

---

## Use Cases

### For Readers

- Save and read paywalled articles offline with consistent formatting
- Organize reading list from Raindrop and GitHub in one place
- Preview articles before opening in browser to save time

### For Developers

- Use as Python library for article extraction in automation workflows
- Extend with custom content sources via modular architecture
- Integrate with existing tools via CLI interface

### For Researchers

- Collect articles in Markdown with metadata for analysis
- Archive content systematically across multiple sources
- Organize sources with tags and bookmarks for research projects

---

## Next Steps

- **[Installation Guide](getting-started/installation.md)** - Detailed setup instructions
- **[Configuration Guide](getting-started/configuration.md)** - Set up authentication and API integrations
- **[TUI Guide](features/tui-guide.md)** - Master the terminal interface
- **[Supported Sites](websites/supported-sites.md)** - Full list of supported websites
- **[Authentication Guide](websites/authentication.md)** - Site-specific login instructions
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[Contributing](development/contributing.md)** - Add your favorite news site

---

## Project Links

- **GitHub**: [xoolive/kiosque](https://github.com/xoolive/kiosque)
- **Issues**: [Report bugs or request features](https://github.com/xoolive/kiosque/issues)
- **License**: MIT
