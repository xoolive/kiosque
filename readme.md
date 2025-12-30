# kiosque

A command-line tool and Python library for downloading and reading articles from paywalled news websites. Extract full article text as Markdown, with support for authentication and integration with Raindrop.io bookmarks.

## Quick Start

```bash
# Launch interactive TUI (Terminal User Interface)
kiosque

# Download article to file
kiosque https://www.lemonde.fr/article output.md

# Print article to stdout (pipe to your favorite pager)
kiosque https://www.nytimes.com/article - | bat - -l md
```

## Command-Line Interface

### Article Download

```bash
# Save article as Markdown (auto-named from URL)
kiosque https://url.com/article

# Save with custom filename
kiosque https://url.com/article output.md

# Print to stdout
kiosque https://url.com/article -

# Verbose mode (shows login & download progress)
kiosque -v https://url.com/article -
```

### Interactive TUI

```bash
# Launch TUI to browse Raindrop.io bookmarks
kiosque
# or explicitly:
kiosque tui
```

#### TUI Keybindings

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate entries |
| `Enter` | Preview article in modal |
| `d` | Download article to file |
| `a` | Archive bookmark in Raindrop.io |
| `o` | Open original URL in browser |
| `r` | Refresh bookmark list |
| `q` | Quit application |
| `Esc` | Close modal / Cancel |

### PDF Download (Latest Issue)

For supported websites that publish periodic PDFs:

```bash
# Download latest PDF issue
kiosque latest_issue https://www.monde-diplomatique.fr/
```

## Python API

### Basic Usage

```python
from kiosque import Website

# Extract article text as Markdown
url = "https://www.lemonde.fr/article"
markdown_text = Website.instance(url).full_text(url)

# Save to file
Website.instance(url).save(url, "article.md")
```

### Advanced Usage

```python
from kiosque import Website
from kiosque.core.config import configuration_file

# Get website instance for a URL
website = Website.instance("https://www.nytimes.com/article")

# Check if authentication is configured
if website.credentials:
    print(f"Username: {website.credentials['username']}")

# Login (if credentials configured)
website.login()

# Get article metadata
url = "https://www.nytimes.com/article"
soup = website.bs4(url)
title = soup.find("h1").text
author = soup.find("meta", {"name": "author"})["content"]

# Extract full article as Markdown
markdown = website.full_text(url)

# Download latest PDF issue (if supported)
pdf_path = website.save_latest_issue()
```

### Configuration File Location

```python
from kiosque.core.config import configuration_file

print(configuration_file)
# Output: /Users/username/.config/kiosque/kiosque.conf
```

## Authentication

Many websites require a subscription to access full articles. Configure credentials in the configuration file:

### Configuration File Format

The configuration file uses INI format with sections for each website:

```ini
# Website credentials (base URL as section name)
[https://www.lemonde.fr/]
username = your.email@example.com
password = your_password

[https://www.nytimes.com/]
username = your_username
password = your_password

# Raindrop.io integration (optional)
[raindrop.io]
token = your_raindrop_api_token
```

### Finding Your Configuration File

```bash
# View configuration file location
python -c "from kiosque.core.config import configuration_file; print(configuration_file)"
```

Default locations:
- Linux: `~/.config/kiosque/kiosque.conf`
- macOS: `~/.config/kiosque/kiosque.conf`
- Windows: `%APPDATA%\kiosque\kiosque.conf`

Or set `XDG_CONFIG_HOME` environment variable to customize the location.

### Raindrop.io Integration

To browse and download bookmarks from Raindrop.io in the TUI:

1. Create a Raindrop.io API token at: https://app.raindrop.io/settings/integrations
2. Add to your configuration file:
   ```ini
   [raindrop.io]
   token = your_api_token_here
   ```
3. Launch the TUI: `kiosque`

### Proxy Configuration (for Geo-blocked Websites)

Some websites are geo-blocked and only accessible from specific regions. Kiosque supports SOCKS and HTTP proxies:

```ini
# Add proxy configuration
[proxy]
url = socks5://localhost:1080
```

Supported formats:
- `socks5://host:port` (recommended)
- `socks4://host:port`
- `http://host:port`
- `https://host:port`

**Example with SSH tunnel:**

```bash
# Create SOCKS5 proxy to server in France
ssh -D 1080 -N user@french-server.com

# Configure in kiosque.conf:
# [proxy]
# url = socks5://localhost:1080
```

**Geo-blocked websites:**
- Courrier International (France/Europe only)
- Les Échos (France/Europe only)

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#403-forbidden-or-406-not-acceptable---geo-blocking) for detailed proxy setup.

## Installation

### From PyPI (Recommended)

```bash
pip install kiosque
```

### Development Installation

For contributing or running the latest development version:

```bash
# Clone repository
git clone https://github.com/yourusername/kiosque.git
cd kiosque

# Install with uv (recommended)
uv sync --dev

# Run development version
uv run kiosque

# Run tests
uv run pytest

# Format and lint code
uv run ruff format .
uv run ruff check .
```

### Requirements

- Python 3.12+
- Dependencies: httpx, beautifulsoup4, textual, pypandoc, stamina, pydantic
- External: pandoc (for HTML to Markdown conversion)

## Supported Websites

A comprehensive list is available in [`websites.md`](websites.md). 

- **30+ news websites** across English, French, and Japanese languages
- **Authentication support** for many paywalled sites (with valid subscription)
- **PDF download** for select publications (e.g., Le Monde Diplomatique)

See the full list with authentication status at [websites.md](websites.md).

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- How to add support for new websites
- Website scraper implementation guide
- Code style and testing guidelines

## Troubleshooting

For common issues and solutions, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Architecture

For an overview of the project structure and design, see [ARCHITECTURE.md](ARCHITECTURE.md).

## License

MIT
