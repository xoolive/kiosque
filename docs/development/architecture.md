# Architecture Overview

## Project Structure

```
kiosque/
├── kiosque/
│   ├── core/           # Core functionality
│   │   ├── client.py   # HTTP client with retry logic
│   │   ├── config.py   # Configuration loading & validation
│   │   └── website.py  # Base Website class
│   ├── website/        # Individual website scrapers (30+ files)
│   │   ├── lemonde.py
│   │   ├── nytimes.py
│   │   └── ...
│   ├── api/            # External API integrations
│   │   ├── raindrop.py # Raindrop.io bookmarks
│   │   └── pocket.py   # Pocket (deprecated)
│   ├── tui/            # Terminal UI
│   │   ├── tui.py      # Textual TUI application
│   │   └── kiosque.tcss # TUI styles
│   └── __init__.py     # CLI entry point
├── tests/              # Test suite
└── pyproject.toml      # Dependencies & metadata
```

## Component Overview

### Core Layer (`kiosque/core/`)

#### `client.py` - HTTP Client

Provides HTTP request wrappers with automatic retry logic:

- **`get_with_retry(url, **kwargs)`\*\* - GET request with exponential backoff
- **`post_with_retry(url, **kwargs)`\*\* - POST request with exponential backoff
- **Retry strategy:** 3 attempts, exponential backoff (stamina library)
- **Timeout:** 30 seconds per request
- **Shared client:** Single `httpx.Client` instance for connection pooling

```python
from kiosque.core.client import get_with_retry

response = get_with_retry("https://example.com/article")
```

#### `config.py` - Configuration Management

Handles loading and validating user configuration:

- **Configuration file:** `~/.config/kiosque/kiosque.conf` (or `$XDG_CONFIG_HOME`)
- **Format:** INI file with website credentials and API tokens
- **Validation:** Pydantic models ensure data integrity
  - `WebsiteCredentials` - Username/password pairs
  - `RaindropConfig` - API token validation
- **Access:** `config_dict` dictionary maps URLs to credentials

```python
from kiosque.core.config import config_dict, configuration_file

credentials = config_dict.get("https://www.lemonde.fr/")
# Returns: {"username": "...", "password": "..."}
```

#### `website.py` - Base Website Class

Abstract base class for all website scrapers:

**Key Components:**

1. **Class Attributes:**
   - `base_url`: Website home URL (required)
   - `login_url`: Authentication endpoint (optional)
   - `alias`: List of short names for CLI (optional)
   - `clean_nodes`: HTML elements to remove (optional)
   - `clean_attributes`: Elements to strip attributes from (optional)
   - `header_entries`: Custom HTTP headers (optional)

2. **Core Methods:**
   - `instance(url)` - Factory method, returns appropriate Website subclass
   - `bs4(url)` - Fetch URL and return BeautifulSoup object
   - `login()` - Authenticate with website
   - `article(url)` - Extract article HTML element
   - `clean(article)` - Remove unwanted elements
   - `full_text(url)` - Convert article to Markdown
   - `save(url, filename)` - Download article to file

3. **Performance Features:**
   - **Module caching:** Website implementations discovered once, cached
   - **Connection pooling:** Shared HTTP client across requests
   - **Retry logic:** Automatic retry with backoff for network failures

```python
from kiosque.core.website import Website

# Get website-specific scraper
website = Website.instance("https://www.lemonde.fr/article")

# Extract article as Markdown
markdown = website.full_text("https://www.lemonde.fr/article")
```

### Website Layer (`kiosque/website/`)

Each file implements a website-specific scraper by subclassing `Website`:

**Implementation Pattern:**

```python
from typing import ClassVar
from ..core.website import Website

class ExampleSite(Website):
    base_url = "https://example.com/"
    login_url = "https://example.com/login"  # If auth required

    # Optional: CSS selectors to remove
    clean_nodes: ClassVar = [
        "figure",
        ("div", {"class": "advertisement"}),
    ]

    # Optional: Elements to strip attributes from
    clean_attributes: ClassVar = ["h2", "blockquote"]

    # Optional: Custom login flow
    @property
    def login_dict(self):
        return {
            "username": self.credentials["username"],
            "password": self.credentials["password"],
        }

    # Required: Extract article content
    def article(self, url):
        soup = self.bs4(url)
        return soup.find("article", class_="main-content")

    # Optional: Additional cleanup
    def clean(self, article):
        article = super().clean(article)
        # Custom transformations
        return article
```

**Key Customization Points:**

1. **`login_dict` property:** Custom authentication payload
2. **`article(url)` method:** Locate article content in page
3. **`clean(article)` method:** Website-specific HTML cleanup
4. **Class attributes:** Declarative cleanup rules

### API Layer (`kiosque/api/`)

#### `raindrop.py` - Raindrop.io Integration

Fetches and manages bookmarks from Raindrop.io:

- **Authentication:** API token from config
- **Data models:** Pydantic models for type safety
  - `RaindropTag` - Bookmark tags
  - `RaindropItem` - Individual bookmark
- **Operations:**
  - `retrieve()` - Fetch all unsorted bookmarks
  - `async_retrieve()` - Async bookmark fetching
  - `action(item_id, action)` - Archive/delete bookmarks

```python
from kiosque.api.raindrop import Raindrop, RaindropItem

raindrop = Raindrop(token="your_token")
items = raindrop.retrieve()  # List[RaindropItem]

for item in items:
    print(f"{item.title}: {item.link}")
```

### TUI Layer (`kiosque/tui/`)

#### `tui.py` - Terminal User Interface

Interactive bookmark browser built with [Textual](https://textual.textualize.io/):

**Components:**

1. **`RaindropTUI` (Main App):**
   - Displays bookmarks from Raindrop.io
   - Auto-refresh every 5 minutes
   - Keyboard-driven interface

2. **`MarkdownModalScreen` (Preview Modal):**
   - Shows article content in scrollable modal
   - Syntax highlighting for Markdown
   - Escape to close

**Key Features:**

- Async bookmark fetching (non-blocking)
- Error handling with user-friendly messages
- Persistent state (selected item across refreshes)
- Browser integration (open URLs externally)

### CLI Layer (`kiosque/__init__.py`)

Command-line interface built with Click:

**Commands:**

```python
@click.group()
def cli():
    """Main entry point"""

@cli.command()
@click.argument("url")
@click.argument("output", default=None)
def download(url, output):
    """Download article to file"""

@cli.command()
def tui():
    """Launch TUI"""
```

**Features:**

- Logging configuration (verbose mode with `-v`)
- Error handling with user-friendly messages
- Configuration file auto-creation

## Data Flow

### Article Download Flow

```
User URL
    ↓
Website.instance(url)  # Get scraper for URL
    ↓
website.login()  # Authenticate if credentials exist
    ↓
website.bs4(url)  # Fetch HTML with retry logic
    ↓
website.article(url)  # Extract article element
    ↓
website.clean(article)  # Remove unwanted elements
    ↓
pypandoc.convert_text()  # HTML → Markdown
    ↓
Save to file or return string
```

### TUI Bookmark Flow

```
Launch TUI
    ↓
Raindrop.async_retrieve()  # Fetch bookmarks
    ↓
Display in ListView
    ↓
User selects item → Enter
    ↓
Website.instance(item.link)  # Get scraper
    ↓
website.full_text(item.link)  # Extract & convert
    ↓
MarkdownModalScreen(markdown)  # Show in modal
```

## Key Design Patterns

### Factory Pattern

`Website.instance(url)` returns the appropriate subclass based on URL:

```python
# Discovers and caches website modules
website = Website.instance("https://www.lemonde.fr/article")
# Returns: LeMonde instance
```

### Template Method Pattern

`Website` class defines the article extraction workflow:

1. `bs4()` - Fetch HTML (implemented in base)
2. `article()` - Extract content (**overridden by subclass**)
3. `clean()` - Remove unwanted elements (**optionally overridden**)
4. Convert to Markdown (implemented in base)

### Configuration as Code

Website cleanup rules declared as class attributes:

```python
clean_nodes: ClassVar = [
    "figure",  # Remove all <figure> tags
    ("div", {"class": "ad"}),  # Remove specific divs
]
```

### Retry Decorator Pattern

Network requests wrapped with automatic retry:

```python
@stamina.retry(on=httpx.HTTPError, attempts=3)
def get_with_retry(url, **kwargs):
    return client.get(url, **kwargs)
```

## Error Handling Strategy

### Network Errors

- **Strategy:** Automatic retry with exponential backoff
- **Implementation:** `stamina` library (3 attempts)
- **Timeout:** 30 seconds per request
- **User feedback:** Logging warnings on retry

### Authentication Errors

- **Missing credentials:** Skip login, attempt public access
- **Invalid credentials:** Raise exception with helpful message
- **Changed login flow:** Log error, suggest updating scraper

### Parsing Errors

- **Missing article element:** NotImplementedError with context
- **Unsupported URL:** ValueError with supported websites list
- **Invalid HTML:** BeautifulSoup handles gracefully

### Configuration Errors

- **Missing config file:** Auto-create template on first run
- **Invalid config format:** Pydantic validation errors
- **Missing API token:** Skip Raindrop.io features

## Performance Considerations

### HTTP Performance

- **Connection pooling:** Single shared `httpx.Client`
- **Timeout:** 30s prevents hanging on slow servers
- **Retry logic:** Max 3 attempts to avoid excessive delays

### Module Loading

- **Lazy imports:** Website modules imported only when needed
- **Module cache:** Discovery happens once, results cached
- **Dict lookup:** O(1) website selection by URL

### TUI Performance

- **Async operations:** Non-blocking bookmark fetching
- **Background refresh:** Auto-refresh doesn't block UI
- **Efficient rendering:** Textual framework handles DOM diffing

## Testing Strategy

See `tests/` directory for implementation:

1. **Unit Tests:**
   - Configuration validation (`test_config.py`)
   - Website base class (`test_website.py`)
   - API models (`test_raindrop.py`)

2. **Integration Tests:**
   - Real login flows (`test_login.py`)
   - HTTP request/response handling
   - End-to-end article extraction (manual testing)

3. **Mocking Strategy:**
   - Mock HTTP client for unit tests
   - Real HTTP for integration tests
   - Mark known-broken logins as `xfail`

## Dependencies

### Core Dependencies

- **httpx** - Modern HTTP client with connection pooling
- **stamina** - Retry logic with exponential backoff
- **beautifulsoup4** - HTML parsing
- **lxml** - Fast HTML parser backend
- **pypandoc** - HTML to Markdown conversion
- **pydantic** - Configuration validation

### TUI Dependencies

- **textual** - Modern TUI framework

### Development Dependencies

- **pytest** - Testing framework
- **ruff** - Fast linting and formatting
- **ty** - Fast type checking (typos alternative)

## Future Architecture Considerations

See `plan.md` for detailed future work, including:

1. **Plugin Architecture:** Modular source system (Raindrop, GitHub, Firefox)
2. **Action Registry:** Context-aware actions based on URL patterns
3. **Async/Await:** Parallel article downloads
4. **Caching:** Local cache for downloaded articles
5. **Extensibility:** User-defined website scrapers

## Related Documentation

- [Quick Start Guide](../index.md) - Getting started with Kiosque
- [Contributing Guide](contributing.md) - How to add new websites
- [Troubleshooting](../troubleshooting.md) - Common issues and solutions
- [Supported Websites](../websites/supported-sites.md) - Complete list of supported sites
