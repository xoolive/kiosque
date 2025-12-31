# Bookmark Management

Manage your bookmarks from Raindrop.io and GitHub Stars in a unified terminal interface.

## Overview

Kiosque provides a powerful TUI for managing bookmarks from multiple sources:

- **Raindrop.io** - Personal bookmark manager with collections, tags, and archive
- **GitHub Stars** - Starred repositories with README previews and topics

All accessible from a single terminal interface with keyboard-driven navigation.

## Quick Start

### 1. Configure API Tokens

**Raindrop.io:**

```ini
# ~/.config/kiosque/kiosque.conf
[raindrop.io]
token = your_raindrop_test_token
```

[Get Raindrop token →](https://app.raindrop.io/settings/integrations)

**GitHub:**

```ini
[github]
token = ghp_your_personal_access_token
```

[Create GitHub token →](https://github.com/settings/tokens)

### 2. Launch TUI

```bash
kiosque
```

### 3. Navigate and Manage

- Press `1` for Raindrop bookmarks
- Press `2` for GitHub Stars
- Press `/` to search
- Press `?` for help

## Features by Source

### Raindrop.io Bookmarks

#### What You Can Do

| Action             | Key      | Description                              |
| ------------------ | -------- | ---------------------------------------- |
| **View**           | Navigate | Browse all your bookmarks with metadata  |
| **Preview**        | `Space`  | Read article content in markdown viewer  |
| **Open**           | `Enter`  | Open bookmark in browser                 |
| **Copy**           | `c`      | Copy URL to clipboard                    |
| **Archive**        | `e`      | Move to archive (hide from main view)    |
| **Delete**         | `d`      | Permanently remove bookmark              |
| **Edit Tags**      | `t`      | Update tags inline                       |
| **Star on GitHub** | `s`      | Star GitHub repos (for GitHub URLs only) |
| **Search**         | `/`      | Filter by title, URL, tags               |

#### Entry Display

Each Raindrop entry shows:

```
🔖 Article Title
   2024-12-31  #python #webdev #tutorial
   Brief excerpt or description...
   https://example.com/article
```

- **Title** - Bookmark title
- **Date** - Creation date (ISO format)
- **Tags** - Hashtag format for easy identification
- **Excerpt** - First few lines of content
- **URL** - Full URL

#### Tag Management

**Flexible Input Formats:**

Kiosque accepts tags in any format:

```
# Space-separated
python programming tutorial

# Comma-separated
python, programming, tutorial

# Hashtags
#python #programming #tutorial

# Mixed
python, #programming tutorial
```

All formats are normalized automatically.

**Workflow:**

1. Navigate to bookmark
2. Press `t`
3. Type tags in any format
4. Press `Enter` to save
5. Tags sync immediately to Raindrop.io

**Note:** Search is disabled while editing tags to prevent interference.

#### Archive vs Delete

- **Archive (`e`)** - Hides from main view, can be restored later in Raindrop web interface
- **Delete (`d`)** - Permanently removes bookmark (cannot be undone)

Use archive for temporary hiding, delete for permanent removal.

#### Cross-Source Actions

**Starring GitHub Repos from Raindrop:**

If a Raindrop bookmark points to a GitHub repository:

1. Navigate to the bookmark
2. Press `s`
3. Repository is starred on GitHub
4. Appears in GitHub Stars tab after refresh

Great for moving bookmarks between systems!

### GitHub Stars

#### What You Can Do

| Action             | Key      | Description                                   |
| ------------------ | -------- | --------------------------------------------- |
| **View**           | Navigate | Browse all starred repositories               |
| **Preview README** | `Space`  | View formatted README in modal                |
| **Open**           | `Enter`  | Open repository in browser                    |
| **Copy**           | `c`      | Copy repository URL to clipboard              |
| **Unstar**         | `u`      | Remove star from repository                   |
| **Search**         | `/`      | Filter by name, topics, language, description |

#### Entry Display

Each GitHub entry shows:

```
★ username/repository-name
   2024-12-31  Python · ⭐ 1.2k · #cli #tui #terminal
   Repository description text...
   https://github.com/username/repo
```

- **Repository** - Full name (owner/repo)
- **Date** - When you starred it
- **Language** - Primary programming language
- **Star count** - Number of stars (⭐)
- **Topics** - Repository topics as hashtags
- **Description** - Repository description
- **URL** - Full GitHub URL

#### README Previews

Press `Space` to preview the repository's README:

- **Markdown rendering** - Formatted text, headings, lists
- **Syntax highlighting** - Code blocks with language detection
- **Scroll support** - Navigate long READMEs
- **Quick assessment** - Evaluate repos before opening

#### Search Capabilities

GitHub search is powerful - searches across:

- Repository name
- Description
- Primary language
- Topics/tags
- Owner name

**Examples:**

- `textual` - Find all Textual-related repos
- `Python` - Filter by language
- `#cli` - Find repos tagged "cli"
- `rust systems` - Multiple terms

## Unified Search

Press `/` to activate search across **all tabs simultaneously**.

### What Gets Searched

**Raindrop:**

- Title
- URL
- Tags
- Excerpt

**GitHub:**

- Repository name
- Description
- Language
- Topics
- Owner

### Search Behavior

- **Debounced** - 300ms delay after you stop typing
- **Case-insensitive** - Finds matches regardless of case
- **Real-time filtering** - Results update as you type
- **Cross-tab** - Same search applies to all tabs
- **Clear with Esc** - Quick reset

### Search Tips

1. **Start broad** - Use general terms, then refine
2. **Use hashtags** - `#tag` for precise tag/topic matching
3. **Language filter** - Type language name for GitHub repos
4. **Multiple terms** - Space-separated terms (AND logic)
5. **Wait briefly** - Let debounce complete for accurate results

## Progressive Loading

The TUI uses smart loading for better UX:

```
1. Launch TUI
   ↓ (immediate)
2. Raindrop loads → Display entries
   ↓ (100ms delay)
3. GitHub loads → Display entries
   ↓
4. Both tabs ready
```

**Benefits:**

- Fast initial load
- Non-blocking UI
- Responsive navigation
- Better perceived performance

## Live Counts

The window title shows real-time statistics:

```
Kiosque (42) · Raindrop (30) · GitHub (12)
```

Updates automatically after:

- Deleting bookmarks
- Archiving bookmarks
- Unstarring repos
- Refreshing tabs
- Searching/filtering

## Workflow Examples

### Daily Reading Workflow

1. **Morning:** Browse Raindrop bookmarks (`1`)
2. **Search:** Filter for topic `/python`
3. **Preview:** Press `Space` to read summaries
4. **Read:** Press `Enter` to open interesting ones
5. **Archive:** Press `e` on completed articles
6. **Clean up:** Press `d` on unwanted bookmarks

### GitHub Discovery Workflow

1. **Switch to GitHub:** Press `2`
2. **Search topic:** `/machine-learning`
3. **Preview READMEs:** Press `Space` to evaluate
4. **Unstar old repos:** Press `u` on outdated ones
5. **Organize:** Cross-reference with Raindrop bookmarks

### Research Organization Workflow

1. **Collect in Raindrop:** Bookmark articles as you find them
2. **Tag immediately:** Press `t` to add topic tags
3. **Review weekly:** Search by tag `/project-name`
4. **Archive completed:** Press `e` on researched topics
5. **Star related repos:** Press `s` on GitHub URLs

### Cross-Source Workflow

1. **Find repo in Raindrop:** GitHub URL bookmarked
2. **Star on GitHub:** Press `s` on the bookmark
3. **Switch tabs:** Press `2` to see GitHub Stars
4. **Refresh:** Press `r` to see newly starred repo
5. **Preview README:** Press `Space` to read details

## API Rate Limits

### Raindrop.io

- **Free account:** 120 requests/minute
- **Operations:**
  - Fetch bookmarks: 1 request per 50 bookmarks
  - Delete: 1 request
  - Archive: 1 request
  - Edit tags: 1 request

Normal usage stays well within limits.

### GitHub

- **With token:** 5,000 requests/hour
- **Operations:**
  - Fetch stars: 1 request per 100 repos
  - Preview README: 1 request per preview
  - Unstar: 1 request
  - Star: 1 request

More than sufficient for typical usage.

## Configuration

### Minimal Setup

```ini
# Raindrop only
[raindrop.io]
token = test_token_abc123
```

or

```ini
# GitHub only
[github]
token = ghp_abc123
```

### Full Setup

```ini
# Both sources
[raindrop.io]
token = test_token_abc123

[github]
token = ghp_abc123def456
```

### Optional: Refresh Intervals

```ini
[tui]
raindrop_refresh_interval = 300  # seconds (default: 300)
github_refresh_interval = 600    # seconds (default: 600)
```

## Troubleshooting

### No bookmarks appear

**Raindrop:**

1. Check token is valid
2. Test: `curl -H "Authorization: Bearer TOKEN" https://api.raindrop.io/rest/v1/user`
3. Ensure `[raindrop.io]` section exists
4. Try refreshing with `r`

**GitHub:**

1. Check token is valid
2. Ensure `[github]` section exists
3. Token needs public_repo scope minimum
4. Try refreshing with `r`

### Tab doesn't appear

Only configured sources show tabs:

- Raindrop tab appears if `[raindrop.io]` token is set
- GitHub tab appears if `[github]` token is set

Configure at least one source.

### Actions not working

- **Wrong tab:** Some actions are tab-specific (`t` for Raindrop only)
- **No selection:** Ensure entry is selected
- **Network issue:** Try refreshing with `r`
- **Rate limit:** Wait a minute and try again

### Search not working

- **Debounced:** Wait 300ms after typing
- **Tag mode:** Cannot search while editing tags (press `Esc`)
- **No results:** Try broader search terms
- **Clear search:** Press `Esc` to reset

### Preview fails

- **No README:** Some repos don't have README files
- **Network issue:** Check internet connection
- **Private repo:** Token needs repo scope
- **Article unavailable:** Website may be down

Try opening in browser with `Enter` instead.

### Slow performance

- **Many bookmarks:** 1000+ bookmarks may slow loading
- **Network latency:** Depends on API response times
- **Use search:** Filter to reduce visible entries
- **Progressive loading:** GitHub loads after Raindrop (100ms delay)

## Keyboard Reference

See the complete [TUI Guide](tui-guide.md) for all keyboard shortcuts and detailed navigation.

**Essential shortcuts:**

| Category     | Key     | Action          |
| ------------ | ------- | --------------- |
| **Search**   | `/`     | Activate search |
| **View**     | `Space` | Preview         |
| **View**     | `Enter` | Open in browser |
| **Navigate** | `j/k`   | Down/Up         |
| **Navigate** | `1/2`   | Switch tabs     |
| **Raindrop** | `t`     | Edit tags       |
| **Raindrop** | `e`     | Archive         |
| **Raindrop** | `d`     | Delete          |
| **GitHub**   | `u`     | Unstar          |
| **General**  | `r`     | Refresh         |
| **General**  | `q`     | Quit            |

## See Also

- **[TUI Guide](tui-guide.md)** - Complete keyboard shortcuts and navigation
- **[Raindrop Integration](../integrations/raindrop.md)** - Raindrop.io setup and API details
- **[GitHub Stars Integration](../integrations/github.md)** - GitHub setup and features
- **[Configuration Guide](../getting-started/configuration.md)** - API token configuration

## Tips for Effective Bookmark Management

### Organization

- **Use descriptive tags** - `#machine-learning` not `#ml`
- **Tag consistently** - Pick a tagging scheme and stick to it
- **Archive completed** - Keep main view focused on current interests
- **Delete duplicates** - Use search to find and remove duplicates

### Discovery

- **Preview first** - Use `Space` to assess before opening
- **Search by topic** - Use `/` to find related bookmarks
- **Cross-reference** - Use both Raindrop and GitHub for complete view
- **Star while reading** - Press `s` on GitHub URLs in Raindrop

### Maintenance

- **Weekly review** - Search `/unread` or by date
- **Archive old content** - Press `e` on completed research
- **Unstar inactive repos** - Press `u` on GitHub tab
- **Refresh tags** - Update tags as topics evolve

Happy bookmarking! 🔖
