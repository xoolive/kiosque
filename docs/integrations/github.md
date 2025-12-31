# GitHub Stars Integration

Browse and manage your GitHub starred repositories directly from Kiosque's TUI alongside Raindrop.io bookmarks.

## Overview

Kiosque provides a unified tabbed interface where you can:

- View all your GitHub starred repositories
- Preview README files with formatted markdown
- Unstar repositories directly from the TUI
- Search across repositories by name, description, language, or topics
- Star GitHub repositories found in your Raindrop bookmarks

## Configuration

### 1. Generate GitHub Personal Access Token

1. Go to [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Click **"Generate new token (classic)"**
3. Give it a descriptive name (e.g., "Kiosque TUI")
4. **Scopes:**
   - For public stars only: No scopes needed
   - For private repositories: Check the `repo` scope
5. Click **"Generate token"** and copy the token (starts with `ghp_`)

### 2. Configure Kiosque

Add to `~/.config/kiosque/kiosque.conf`:

```ini
[github]
token = ghp_your_personal_access_token_here
```

### 3. Start the TUI

```bash
kiosque
```

The GitHub Stars tab will appear automatically if the token is configured.

## Features

### Core Functionality

- **Fetch starred repositories** - Automatically retrieves all your GitHub stars with pagination
- **Repository metadata** - Shows name, description, star count, language, topics, and homepage
- **README preview** - View repository README files with formatted markdown rendering
- **Unstar repositories** - Remove stars directly from the TUI
- **Star from Raindrop** - Star GitHub repos found in Raindrop bookmarks
- **Search across sources** - Filter repositories by name, description, language, or topics

### UI Features

- **Tabbed interface** - Separate tabs for Raindrop bookmarks and GitHub Stars
- **Progressive loading** - Raindrop loads first, GitHub loads 100ms later (non-blocking)
- **Dynamic tab display** - Only shows GitHub tab if token is configured
- **Count tracking** - Window title shows counts: `Kiosque (42) · Raindrop (30) · GitHub (12)`
- **Debounced search** - Search waits 300ms after last keystroke to avoid lag

### Entry Display

Each GitHub repository entry shows:

- Repository full name (owner/repo)
- Date starred (ISO format)
- Language · ⭐ star count · #topic1 #topic2 #topic3
- Description

## Usage

### Keyboard Shortcuts

**Tab Navigation:**

| Key | Action                     |
| --- | -------------------------- |
| `1` | Switch to Raindrop tab     |
| `2` | Switch to GitHub Stars tab |

**GitHub-specific Actions:**

| Key            | Action                                                 |
| -------------- | ------------------------------------------------------ |
| `u`            | Unstar repository                                      |
| `Space`        | Preview README content                                 |
| `o` or `Enter` | Open repository in browser                             |
| `c`            | Copy repository URL to clipboard                       |
| `s`            | Star GitHub repo (from Raindrop tab, GitHub URLs only) |

**Common Actions:**

| Key               | Action                            |
| ----------------- | --------------------------------- |
| `/`               | Start search (searches both tabs) |
| `Esc` or `Ctrl+C` | Clear search                      |
| `r`               | Refresh all sources               |
| `q`               | Quit                              |

### Search Functionality

The search bar filters entries across **both** tabs simultaneously:

- Searches repository name (e.g., "textual")
- Searches description text
- Searches language (e.g., "Python")
- Searches topics/tags (e.g., "tui")

**Search is debounced:** It waits 300ms after you stop typing before filtering, preventing lag while you type.

## API Rate Limits

GitHub API rate limits:

- **With authentication** (token): 5,000 requests/hour
- **Without authentication**: 60 requests/hour (insufficient for this feature)

Each operation consumes:

- Fetch stars: 1 request per 100 repositories (paginated)
- Preview README: 1 request per preview
- Unstar: 1 request per unstar operation

The authenticated rate limit is more than sufficient for normal usage.

## Troubleshooting

### Tab doesn't appear

- Verify token is configured in `~/.config/kiosque/kiosque.conf`
- Check token has not expired
- Ensure `[github]` section is present

### "Forbidden" or rate limit errors

- Verify token is valid:
  ```bash
  curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
  ```
- Check you haven't exceeded rate limit (unlikely with 5,000/hour)
- Ensure token has required scopes if accessing private repos

### README preview shows error

- Some repositories don't have README files
- Repository might be deleted or made private
- Network connectivity issue

### Search not working

- Search is debounced - wait 300ms after typing
- Ensure search input has focus (press `/`)
- Try clearing search with `Esc` and starting over

## Security Notes

- **Your GitHub token is like a password** - don't share it
- Store your config file securely (it should be readable only by you)
- Tokens can be revoked at any time from GitHub settings
- Consider using a token with minimal scopes for security

## Technical Details

### Architecture

- **Async API calls** - All GitHub operations are async
- **Progressive loading** - Uses `asyncio.create_task()` with delayed GitHub fetch
- **Debounced search** - Uses `asyncio.TimerHandle` for delayed filter execution
- **Reactive counts** - Window title updates automatically on changes

### Data Flow

1. On mount: Load Raindrop immediately
2. After 100ms: Load GitHub stars in background
3. On data arrival: Update entries and counts
4. On search: Debounced filter across all tabs (300ms delay)
5. On action: Update local state and refresh counts

## Future Enhancements

Potential improvements:

- Add ability to star new repositories from TUI
- Cache README content for faster previews
- Show repository activity/commit history
- Filter by language or topic
- Sort by star date, star count, or name
- Export starred repos to various formats

## Resources

- GitHub API Documentation: https://docs.github.com/en/rest
- Personal Access Tokens: https://github.com/settings/tokens
- Textual TUI Framework: https://textual.textualize.io/
