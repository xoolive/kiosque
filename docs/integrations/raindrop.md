# Raindrop.io Integration

Browse and manage your Raindrop.io bookmarks directly from Kiosque's TUI with support for previews, archiving, deletion, and tag editing.

## Overview

Kiosque provides a terminal UI for Raindrop.io that allows you to:

- Browse all your bookmarks with rich metadata
- Preview article content in a modal viewer
- Archive or delete bookmarks directly
- Edit tags inline with flexible input formats
- Search by title, URL, or tags
- Star GitHub repositories found in bookmarks

## Configuration

### 1. Generate Raindrop.io API Token

1. Go to [Raindrop.io Settings → Integrations](https://app.raindrop.io/settings/integrations)
2. Click **"Create new app"** or use an existing test token
3. For a test token:
   - Scroll to **"Test token"** section
   - Click **"Create test token"**
   - Copy the token
4. For a production app:
   - Fill in app details (name, description, icon)
   - Click **"Create"**
   - Copy the token from the app details page

### 2. Configure Kiosque

Add to `~/.config/kiosque/kiosque.conf`:

```ini
[raindrop.io]
token = your_raindrop_api_token_here
```

### 3. Start the TUI

```bash
kiosque
```

Your Raindrop bookmarks will appear in the main tab.

## Features

### Core Functionality

- **Browse bookmarks** - View all your Raindrop.io bookmarks with metadata
- **Preview content** - See article content in a modal with markdown rendering
- **Archive bookmarks** - Move bookmarks to archive
- **Delete bookmarks** - Remove bookmarks permanently
- **Edit tags** - Update tags inline with smart parsing
- **Search** - Filter by title, URL, or tags with debounced search (300ms)
- **Star GitHub repos** - Star repositories directly from Raindrop (GitHub URLs only)

### Tag Editing

Press `t` on any bookmark to edit tags. The tag editor supports flexible input formats:

**Input Formats:**

- Space-separated: `python programming tui`
- Comma-separated: `python, programming, tui`
- With hashtags: `#python #programming #tui`
- Mixed: `python, #programming tui`

All formats are automatically normalized to a consistent list of tags.

**Tag Mode Behavior:**

- Search is disabled while editing tags (prevents accidental filtering)
- Press `Enter` to save changes
- Press `Esc` to cancel editing
- Tags are synchronized immediately with Raindrop.io

### Entry Display

Each Raindrop bookmark entry shows:

- Title
- Date created (ISO format)
- Tags: #tag1 #tag2 #tag3
- Excerpt/description (if available)
- URL

## Usage

### Keyboard Shortcuts

**Navigation:**

| Key                   | Action                              |
| --------------------- | ----------------------------------- |
| `↑` / `↓` / `j` / `k` | Navigate entries                    |
| `Ctrl+d` / `Ctrl+u`   | Scroll down/up by 5 entries         |
| `g` / `G`             | Jump to top/bottom                  |
| `1` / `2`             | Switch between Raindrop/GitHub tabs |

**Raindrop-specific Actions:**

| Key            | Action                                          |
| -------------- | ----------------------------------------------- |
| `Space`        | Preview article/content in modal                |
| `Enter` or `o` | Open in browser                                 |
| `c`            | Copy URL to clipboard                           |
| `d`            | Delete bookmark                                 |
| `e`            | Archive bookmark                                |
| `t`            | Edit tags                                       |
| `s`            | Star on GitHub (Raindrop tab, GitHub URLs only) |

**Common Actions:**

| Key               | Action                                  |
| ----------------- | --------------------------------------- |
| `/`               | Start search (searches across all tabs) |
| `Esc` or `Ctrl+C` | Clear search / Cancel tag editing       |
| `r`               | Refresh current tab                     |
| `q`               | Quit                                    |

### Search Functionality

Press `/` to activate search. The search filters bookmarks by:

- Title
- URL
- Tags (matches individual tag names)

**Search is debounced:** It waits 300ms after you stop typing before filtering, preventing lag while you type.

**Note:** Search is automatically disabled when editing tags to prevent interference.

## API Rate Limits

Raindrop.io API limits:

- **Free account**: 120 requests/minute
- **Premium account**: Higher limits (contact Raindrop.io support)

Each operation consumes:

- Fetch bookmarks: 1 request per 50 bookmarks (paginated)
- Delete bookmark: 1 request
- Archive bookmark: 1 request (updates bookmark)
- Edit tags: 1 request (updates bookmark)

Normal usage stays well within rate limits.

## Troubleshooting

### Tab is empty or shows no bookmarks

- Verify token is configured in `~/.config/kiosque/kiosque.conf`
- Check token has not expired or been revoked
- Test token with curl:
  ```bash
  curl -H "Authorization: Bearer YOUR_TOKEN" https://api.raindrop.io/rest/v1/user
  ```
- Ensure `[raindrop.io]` section is present in config

### "Unauthorized" or authentication errors

- Token may be invalid or expired
- Generate a new token from Raindrop.io settings
- Ensure token is copied correctly (no extra spaces)

### Changes not syncing

- Check internet connectivity
- Verify you have write permissions with your token
- Test tokens have full access, production apps might have restricted scopes

### Tag editing issues

- Make sure you're in tag edit mode (press `t`)
- Tags are saved on `Enter` key
- Use any format: spaces, commas, or hashtags
- Check Raindrop.io web interface to verify changes

### Preview not loading

- Some URLs may not be accessible
- Article extraction might fail for certain sites
- Network connectivity issue
- Try opening in browser with `Enter` instead

## Security Notes

- **Your Raindrop.io token is like a password** - don't share it
- Store your config file securely (it should be readable only by you)
- Tokens can be revoked at any time from Raindrop.io settings
- Test tokens expire after 30 days - consider using a production app for long-term use

## Technical Details

### Architecture

- **Async API calls** - All Raindrop operations are async
- **Debounced search** - Uses `asyncio.TimerHandle` for delayed filter execution
- **Tag mode state** - Search is disabled during tag editing to prevent conflicts
- **Reactive UI** - Window title and counts update automatically

### Data Flow

1. On mount: Fetch bookmarks from Raindrop.io API (paginated)
2. Display entries in scrollable list
3. On action (delete/archive/edit): Update via API
4. On search: Debounced filter (300ms delay)
5. On tag edit: Toggle tag mode, disable search, save on Enter

### API Endpoints Used

- `GET /rest/v1/raindrops/0` - Fetch all bookmarks
- `PUT /rest/v1/raindrop/{id}` - Update bookmark (archive, edit tags)
- `DELETE /rest/v1/raindrop/{id}` - Delete bookmark

## Future Enhancements

Potential improvements:

- Create new bookmarks from TUI
- Move bookmarks between collections
- Bulk operations (delete/archive multiple)
- Filter by collection or date
- Sort by date, title, or domain
- Export bookmarks to various formats
- Offline mode with local cache

## Resources

- Raindrop.io API Documentation: https://developer.raindrop.io/
- API Token Settings: https://app.raindrop.io/settings/integrations
- Raindrop.io Help Center: https://help.raindrop.io/
