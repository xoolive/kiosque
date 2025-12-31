# Kiosque Development Roadmap

**Last Updated:** 2025-12-31  
**Current Status:** Core Complete - Active Development

---

## Project Overview

Kiosque is a multi-purpose news and bookmark management tool with three main capabilities:

1. **Article Extraction** - Download full-text articles from 32+ paywalled news websites (CLI/API)
2. **Bookmark Management** - TUI for browsing and managing Raindrop.io bookmarks and GitHub Stars
3. **Content Aggregation** - Unified interface for multiple content sources (expandable to browsers, RSS, etc.)

---

## Completed Work (2025)

### Core Infrastructure ✅

- Modern Python tooling (uv, ruff, ty type checking)
- Retry logic with stamina (3 attempts, exponential backoff)
- Async infrastructure (async_client, async methods with TODO migration path)
- Configuration validation with Pydantic models
- Module caching for performance
- Comprehensive test suite (25 passing, 2 xfailed for geo-blocked logins)
- CI/CD with GitHub Actions (formatting, linting, type checking)

### Website Support ✅

- 32+ supported news websites across English, French, and Japanese
- 6 working authenticated logins (OAuth2 PKCE implementations for modern sites)
- SOCKS/HTTP proxy support for geo-blocked websites
- Article extraction with Markdown conversion
- PDF download for select publications

### NYT Authentication Improvements (2025-12-31) ✅

- **Simplified to Cookie-Based Auth**:
  - Removed Playwright dependency (185 lines of code deleted)
  - NYT has DataDome anti-bot protection that blocks automated browsers
  - Cookie-based authentication is more reliable and simpler to maintain
  - User extracts NYT-S cookie from browser once (lasts months)
  - Comprehensive setup guide in [NYT Cookie Setup](../websites/nyt-cookie-setup.md)
- **HTTP Client Headers Updated**:
  - Upgraded User-Agent from Firefox 115 to Chrome 131
  - Added modern browser fingerprint (AVIF, WebP, Sec-Fetch-\* headers)
  - Improved compatibility with modern websites
- **Link Cleaning**:
  - Removed `rel`, `target`, `class` attributes from extracted article links
  - Clean markdown output with only `href` attribute preserved

### TUI Improvements ✅

- **Refactored Architecture** (2025-12-31):
  - Split monolithic `tui.py` (700+ lines) into modular structure:
    - `tui/tui.py` - Main app and shared components
    - `tui/raindrop.py` - Raindrop.io entry widget
    - `tui/github.py` - GitHub Stars entry widget
  - Fixed circular import issues with lazy imports
  - Proper separation of concerns

- **Raindrop Tag Editing** (2025-12-31):
  - Press `t` on any Raindrop entry to edit tags
  - Smart tag parsing (space/comma separated, with/without #)
  - Live entry updates after saving
  - Full error handling and notifications
  - Fixed search bar filtering during tag editing (checks tag_mode flag)

- **Enhanced Search** (2025-12-31):
  - Search now matches bookmark titles, URLs, AND tags
  - Case-insensitive partial matching
  - Works across all content sources
  - 300ms debounced for performance

- **Multi-Source Tabbed Interface**:
  - Raindrop.io tab with bookmarks management
  - GitHub Stars tab with repository browsing
  - Dynamic tabs (only shows configured sources)
  - Progressive loading (Raindrop first, GitHub 100ms later - non-blocking)
  - Unified search across all tabs (300ms debounced)
  - Window title with counts: `Kiosque (42) · Raindrop (30) · GitHub (12)`

- **Cross-Tab Actions**:
  - Preview GitHub README from Raindrop bookmarks
  - Star GitHub repos from Raindrop tab (with progressive notifications)
  - Dynamic footer bindings ('s' key only for GitHub URLs)
  - Automatic GitHub tab refresh after starring

- **UX Enhancements**:
  - Loading notifications before async operations
  - Beautiful YAML frontmatter rendering in previews
  - Configurable refresh interval (default: 10 min)
  - New articles appear at top (not bottom)
  - Rich Text styling for multi-color tags display

### Documentation ✅

- Comprehensive [Quick Start Guide](../index.md) with API examples and TUI keybindings
- [Architecture Documentation](architecture.md) - System design and patterns
- [Contributing Guide](contributing.md) - Website scraper implementation guide
- [Troubleshooting Guide](../troubleshooting.md) - Common issues and proxy setup
- [GitHub Integration Guide](../integrations/github.md) - GitHub Stars feature documentation
- [Raindrop Integration Guide](../integrations/raindrop.md) - Raindrop.io TUI documentation
- [NYT Cookie Setup](../websites/nyt-cookie-setup.md) - New York Times authentication

---

## Active Development

### Current Sprint

#### 1. Textual Link Navigation Issue 🐛

**Priority:** High  
**Status:** Blocked - Awaiting Textual Fix

**Problem:**
When clicking external HTTP/HTTPS links in `MarkdownViewer`, Textual attempts to navigate to them as local file paths, causing `FileNotFoundError`.

**Root Cause:**

- `MarkdownViewer._on_markdown_link_clicked()` calls `self.go(href)` for ALL links
- The `go()` method passes href to `Navigator.go()` which treats it as a file path
- `Navigator.go()` does: `new_path = self.location.parent / Path(href)`
- Creates invalid path like `/current/dir/https:/github.com/...` → FileNotFoundError

**Current Behavior:**

1. Click link → Browser opens correctly ✅
2. `_on_markdown_link_clicked()` tries to navigate to href as file ❌
3. FileNotFoundError displayed in TUI ❌

**Attempted Solutions:**

- ❌ Setting `open_links=False` - Only prevents browser opening, not navigation
- ❌ Overriding in parent screen - Handler is on MarkdownViewer widget
- ❌ Custom event handlers - Still triggers file navigation

**Issue Filed:**

- Created comprehensive issue report in `TEXTUAL_ISSUE.md`
- Includes code locations, reproduction steps, suggested fixes
- Ready to file at https://github.com/Textualize/textual/issues

**Workaround:**
None currently available without subclassing MarkdownViewer.

**Impact:**

- Links work (browser opens) but error message appears
- UX degradation but not blocking core functionality
- Affects all article previews with external links

**Files:**

- `/textual/widgets/_markdown.py:1631-1633` - `_on_markdown_link_clicked()`
- `/textual/widgets/_markdown.py:1609-1616` - `go()` method
- `/textual/widgets/_markdown.py:153-155` - `Navigator.go()`
- `TEXTUAL_ISSUE.md` - Issue report ready to submit

---

#### 2. TUI Code Refactoring ✅

**Priority:** High  
**Status:** Completed (2025-12-31)

**Completed:**

- ✅ Split `tui.py` into `tui.py`, `raindrop.py`, `github.py`
- ✅ Fixed GitHub tags display with Rich Text inline styling
- ✅ Removed Horizontal layout complexity
- ✅ Language/stars in blue (#4c78ae), topics in gray italic (#79806e)
- ✅ All imports working correctly
- ✅ All ruff checks passing

**Files:**

- `kiosque/tui/tui.py` - Main app (294 lines removed)
- `kiosque/tui/raindrop.py` - Raindrop Entry class (229 lines)
- `kiosque/tui/github.py` - GitHub GitHubEntry class (119 lines)
- `kiosque/tui/kiosque.tcss` - Simplified CSS

---

#### 2. TUI Code Refactoring ✅

**Priority:** High  
**Status:** Completed (2025-12-31)

**Completed:**

- ✅ Split `tui.py` into `tui.py`, `raindrop.py`, `github.py`
- ✅ Fixed GitHub tags display with Rich Text inline styling
- ✅ Removed Horizontal layout complexity
- ✅ Language/stars in blue (#4c78ae), topics in gray italic (#79806e)
- ✅ All imports working correctly
- ✅ All ruff checks passing

**Files:**

- `kiosque/tui/tui.py` - Main app (294 lines removed)
- `kiosque/tui/raindrop.py` - Raindrop Entry class (229 lines)
- `kiosque/tui/github.py` - GitHub GitHubEntry class (119 lines)
- `kiosque/tui/kiosque.tcss` - Simplified CSS

---

#### 3. Raindrop Tag Editing ✅

**Priority:** High  
**Status:** Completed (2025-12-31)

**Goal:** Add/remove tags on Raindrop bookmarks directly from TUI

**Implementation:**

- ✅ Reuse search bar for tag input (press `t` to enter tag mode)
- ✅ Tag mode UI with placeholder: "Edit tags (space-separated, with or without #)"
- ✅ Smart tag parsing: supports space-separated, comma-separated, with/without # prefix
- ✅ Automatic deduplication of tags
- ✅ Save tags via Raindrop API on Enter
- ✅ Show success/error notifications
- ✅ Cancel with Esc (restores original tags on error)
- ✅ Live entry update after tag change (recompose)

**Features:**

- **Flexible Input Formats:**
  - Space-separated: `python javascript rust`
  - Comma-separated: `python, javascript, rust`
  - With # prefix: `#python #javascript #rust`
  - Mixed format: `#python, javascript rust`
  - Automatic deduplication and whitespace handling

- **User Experience:**
  - Press `t` on any Raindrop entry to edit tags
  - Search bar switches to tag mode with current tags pre-filled
  - Enter to save, Esc to cancel
  - Progressive notifications (updating → success/error)
  - Entry automatically refreshes to show new tags
  - Focus returns to entry after edit

**API Methods Added:**

```python
# kiosque/api/raindrop.py
async def update_tags_async(self, raindrop_id: int, tags: list[str]) -> dict[str, Any]
def update_tags(self, raindrop_id: int, tags: list[str]) -> dict[str, Any]
```

**Files Modified:**

- ✅ `kiosque/api/raindrop.py` - Added update_tags methods (async + sync)
- ✅ `kiosque/tui/raindrop.py` - Added 't' binding and action_edit_tags()
- ✅ `kiosque/tui/tui.py` - SearchBar tag mode logic, parse_tags(), update_raindrop_tags()

**Testing:**

- ✅ All ruff checks passing
- ✅ All imports working
- ✅ Tag parsing logic tested (7 test cases, all passing)
- ✅ API methods verified (async and sync versions)

---

## Upcoming Features

### Browser Bookmarks Integration

**Priority:** Medium  
**Status:** Planned - Firefox Sync API

**Previous Plan:**

- ~~Read Firefox bookmarks from places.sqlite~~ ❌ Not smart - DB locking issues

**Selected Approach: Firefox Sync API** ✅

**Why Firefox Sync API:**

- No direct database access (avoids locking issues)
- Cross-platform (works on all devices with Firefox Account)
- Read-only access is safe and reliable
- Official Firefox Account OAuth integration
- Can be extended to other browsers later

**Implementation Plan:**

**Phase 1: Firefox Sync Authentication**

- Implement Firefox Account OAuth flow
- Store OAuth tokens in kiosque config
- Handle token refresh automatically

**Phase 2: Sync API Integration**

- Fetch bookmarks via Firefox Sync API endpoints
- Parse bookmark folder structure
- Cache bookmarks locally for performance
- Periodic sync (configurable interval)

**Phase 3: TUI Integration**

- Create bookmarks tab in TUI
- Display folder hierarchy
- Search and filter bookmarks
- Open in browser action
- Preview bookmark content

**Firefox Sync API Details:**

**OAuth Flow:**

```python
# Required scopes
scopes = ["https://identity.mozilla.com/apps/sync"]

# OAuth endpoints
auth_url = "https://accounts.firefox.com/authorization"
token_url = "https://oauth.accounts.firefox.com/v1/token"

# Sync API
sync_url = "https://sync-1-us-west1-g.sync.services.mozilla.com"
```

**Configuration Example:**

```ini
[firefox]
# Firefox Account credentials (OAuth tokens stored securely)
client_id = your_client_id
client_secret = your_client_secret
# Sync settings
sync_interval = 600  # 10 minutes
```

**API Methods:**

```python
# kiosque/api/firefox.py
class FirefoxSyncAPI:
    async def authenticate(self) -> None:
        """OAuth flow for Firefox Account"""

    async def fetch_bookmarks(self) -> list[Bookmark]:
        """Fetch all bookmarks from Sync API"""

    async def sync(self) -> None:
        """Sync bookmarks (fetch and cache)"""
```

**Files to Create:**

- `kiosque/api/firefox.py` - Firefox Sync API client
- `kiosque/tui/firefox.py` - Firefox bookmarks tab widget

**Future Browser Support:**

- Chrome Sync API (requires Google OAuth)
- Brave Sync API (own protocol)
- Safari iCloud Bookmarks (macOS only)
- Generic export-based fallback for other browsers

### Documentation Website

**Priority:** Medium  
**Status:** Planning

**Technology Options:**

- **MkDocs** - Simple, Markdown-based (Recommended)
- **Sphinx** - Python ecosystem standard
- **Docusaurus** - Modern, React-based
- **VitePress** - Vue-based, fast

**Recommended:** MkDocs with Material theme

**Structure:**

```
docs/
├── index.md                    # What is Kiosque?
├── getting-started/
│   ├── installation.md         # Installation guide
│   ├── configuration.md        # Config file setup
│   └── first-steps.md          # Quick start tutorial
├── features/
│   ├── article-extraction.md   # CLI for downloading articles
│   ├── bookmark-management.md  # TUI for Raindrop/GitHub
│   └── tui-guide.md            # Complete TUI reference
├── integrations/
│   ├── raindrop.md             # Raindrop.io setup
│   ├── github-stars.md         # GitHub Stars setup
│   └── browsers.md             # Browser bookmarks (future)
├── websites/
│   ├── supported-sites.md      # List of 32+ websites
│   ├── authentication.md       # Login setup per site
│   └── adding-sites.md         # Contributing new sites
├── api/
│   ├── python-api.md           # Using kiosque as library
│   └── reference.md            # API documentation
├── development/
│   ├── architecture.md         # System design
│   ├── contributing.md         # How to contribute
│   └── roadmap.md              # This roadmap
└── troubleshooting.md          # Common issues
```

**Implementation:**

```bash
# Setup
pip install mkdocs-material
mkdocs new .

# Development
mkdocs serve  # Local preview at http://localhost:8000

# Deployment
mkdocs build  # Generates static site in site/
# Deploy to GitHub Pages, Netlify, or Vercel
```

**Configuration:**

```yaml
# mkdocs.yml
site_name: Kiosque
site_description: News article extraction and bookmark management
theme:
  name: material
  palette:
    primary: blue
  features:
    - navigation.tabs
    - navigation.sections
    - toc.integrate
    - search.suggest

nav:
  - Home: index.md
  - Getting Started:
      - Installation: getting-started/installation.md
      - Configuration: getting-started/configuration.md
  - Features:
      - Article Extraction: features/article-extraction.md
      - Bookmark Management: features/bookmark-management.md
  - Integrations:
      - Raindrop.io: integrations/raindrop.md
      - GitHub Stars: integrations/github-stars.md
  - Development:
      - Contributing: development/contributing.md
      - Architecture: development/architecture.md
```

**Hosting Options:**

- GitHub Pages (free, easy GitHub Actions integration)
- ReadTheDocs (Python project standard)
- Netlify/Vercel (modern CI/CD)

---

## README Clarification

**Priority:** High  
**Status:** Pending

**Current Issue:**  
README is focused on article extraction, but Kiosque now does much more

**Proposed Structure:**

````markdown
# Kiosque

A unified tool for news article extraction and bookmark management.

## What is Kiosque?

Kiosque is three tools in one:

1. **Article Extractor (CLI/API)** - Download full-text articles from 32+ paywalled websites
2. **Bookmark Manager (TUI)** - Browse and manage bookmarks from Raindrop.io and GitHub Stars
3. **Content Aggregator** - Unified interface for multiple content sources

## Quick Start

### Extract Articles (CLI)

```bash
# Download article to Markdown
kiosque https://www.lemonde.fr/article output.md

# Print to stdout
kiosque https://www.nytimes.com/article -
```
````

### Manage Bookmarks (TUI)

```bash
# Launch interactive TUI
kiosque

# Or explicitly
kiosque tui
```

### Use as Python Library

```python
from kiosque import Website

markdown = Website.instance(url).full_text(url)
```

## Core Features

### Article Extraction

- 32+ supported news websites (Le Monde, NYT, Guardian, etc.)
- Full authentication support for paywalled sites
- Markdown output with metadata
- Proxy support for geo-blocked sites
- PDF download for select publications

### Bookmark Management

- Raindrop.io integration (browse, archive, delete, preview)
- GitHub Stars integration (browse, unstar, preview README)
- Cross-tab actions (star GitHub repos from Raindrop)
- Unified search across sources
- Beautiful previews with syntax highlighting

### Content Aggregation

- Tabbed interface for multiple sources
- Dynamic loading (non-blocking)
- Configurable refresh intervals
- Smart context-aware actions

## Use Cases

**For Readers:**

- Save and read paywalled articles offline
- Organize reading list from multiple sources
- Preview articles before opening in browser

**For Developers:**

- Python library for article extraction
- Integrate with automation workflows
- Extend with custom content sources

**For Researchers:**

- Collect articles with consistent formatting
- Archive content in Markdown
- Organize sources with tags and bookmarks

## Installation

[... existing installation section ...]

```

**Key Changes:**
- Lead with "three tools in one" concept
- Show all three use cases upfront (CLI, TUI, API)
- Separate sections for each capability
- Add "Use Cases" to help users understand fit
- More prominent TUI documentation

---

## Future Considerations

### Video Download Integration
- Detect video URLs (yt-dlp supported sites)
- Download action with progress display
- Configurable quality/format
- Queue management

### RSS Feed Support
- Add RSS feeds as content source
- Fetch and display recent articles
- Mark as read functionality
- Integration with article extraction

### Export/Backup Features
- Export bookmarks to various formats
- Backup article archive
- Sync between devices

### Search Improvements
- Full-text search in article content
- Advanced filters (date range, tags, source)
- Search history
- Saved search queries

---

## Implementation Priority

### Immediate (Current Sprint)
1. ✅ TUI code refactoring (completed 2025-12-31)
2. ✅ Raindrop tag editing (completed 2025-12-31)
3. ✅ Firefox Sync API decision (completed 2025-12-31)
4. 🔄 README clarification (pending)

### Short-term (Next Month)
5. Documentation website (MkDocs setup)
6. Firefox Sync API implementation (OAuth + bookmarks fetch)
7. Additional TUI polish (colors, spacing, UX)
8. **Textual upstream fix** - Wait for MarkdownViewer link navigation fix

### Medium-term (Next Quarter)
8. Firefox bookmarks tab in TUI
9. Documentation content completion
10. Video download integration (if requested)

### Long-term (Future)
11. RSS feed support
12. Other browser sync APIs (Chrome, Brave, Safari)
13. Mobile companion app (consider)

---

## Technical Debt

### Code Quality
- ✅ Type hints modernized
- ✅ All ruff checks passing
- ✅ TUI properly modularized
- ⏳ Full async migration (11 websites need refactoring)
- ⏳ Improve test coverage (currently 25 tests)

### Documentation
- ✅ README comprehensive
- ✅ Architecture documented
- ✅ Contributing guide complete
- ⏳ Documentation website (planned)
- ⏳ API reference documentation

### Infrastructure
- ✅ CI/CD working
- ✅ Proxy support implemented
- ⏳ Release automation (consider)
- ⏳ PyPI publishing workflow

---

## Contributing

See [Contributing Guide](contributing.md) for:
- How to add new websites
- Code style guidelines
- Testing requirements
- Development setup

## Questions/Feedback

- Open an issue on GitHub
- Check existing documentation ([Quick Start](../index.md), [Architecture](architecture.md), [Troubleshooting](../troubleshooting.md))
- Review this roadmap for planned features
```
