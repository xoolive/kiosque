# Configuration

This guide covers how to configure Kiosque for website authentication, API integrations, and proxy settings.

## Configuration File

Kiosque uses an INI-format configuration file to store credentials and settings.

### File Location

Default locations:

- **Linux/macOS:** `~/.config/kiosque/kiosque.conf`
- **Windows:** `%APPDATA%\kiosque\kiosque.conf`

You can customize the location by setting the `XDG_CONFIG_HOME` environment variable.

**Find your config file:**

```bash
python -c "from kiosque.core.config import configuration_file; print(configuration_file)"
```

### File Format

The configuration file uses INI format with sections for each website or service:

```ini
# Website credentials (base URL as section name)
[https://www.lemonde.fr/]
username = your.email@example.com
password = your_password

[https://www.nytimes.com/]
cookie_nyt_s = your_nyt_cookie_value

# API integrations
[raindrop.io]
token = your_raindrop_api_token

[github]
token = ghp_your_github_personal_access_token

# Proxy configuration (optional)
[proxy]
url = socks5://localhost:1080
```

## Website Authentication

Many news websites require a subscription to access full articles. Configure your credentials to enable authenticated access.

### Username/Password Authentication

For most websites, add your subscription credentials:

```ini
[https://www.lemonde.fr/]
username = your.email@example.com
password = your_password

[https://www.theguardian.com/]
username = your.email@example.com
password = your_password
```

**Supported websites:** See [Authentication Guide](../websites/authentication.md) for a complete list of websites with authentication support.

### Cookie-Based Authentication (NYT)

The New York Times uses cookie-based authentication due to CAPTCHA protection:

```ini
[https://www.nytimes.com/]
cookie_nyt_s = your_cookie_value_here
```

**Detailed setup:** See [NYT Cookie Setup Guide](../websites/nyt-cookie-setup.md) for step-by-step instructions on extracting the cookie from your browser.

**Notes:**

- Cookie typically lasts 3-6 months before renewal
- Without a cookie, you'll only get article previews (~7 paragraphs)
- With a valid cookie, you get full article access

## API Integrations

### Raindrop.io

Configure Raindrop.io integration to browse and manage your bookmarks in the TUI:

**1. Create API Token:**

- Visit https://app.raindrop.io/settings/integrations
- Click "Create new app"
- Generate a test token
- Copy the token

**2. Add to configuration:**

```ini
[raindrop.io]
token = your_api_token_here
```

**3. Launch TUI:**

```bash
kiosque
```

**Features:** Browse bookmarks, preview articles, edit tags, archive, delete, and search. See [Raindrop Integration Guide](../integrations/raindrop.md) for details.

### GitHub Stars

Configure GitHub integration to browse your starred repositories in the TUI:

**1. Create Personal Access Token:**

- Visit https://github.com/settings/tokens
- Click "Generate new token" → "Generate new token (classic)"
- Name: "Kiosque TUI"
- Scopes: Select `public_repo` (or `repo` for private repos)
- Click "Generate token" and copy it

**2. Add to configuration:**

```ini
[github]
token = ghp_your_github_personal_access_token_here
```

**3. Launch TUI and switch to GitHub tab:**

```bash
kiosque
# Press '2' to view GitHub Stars tab
```

**Features:** Browse starred repos, preview READMEs, unstar repositories, and search. See [GitHub Integration Guide](../integrations/github.md) for details.

## Proxy Configuration

Some websites are geo-blocked and only accessible from specific regions. Kiosque supports SOCKS and HTTP proxies.

### Proxy Setup

Add proxy configuration to your config file:

```ini
[proxy]
url = socks5://localhost:1080
```

**Supported formats:**

- `socks5://host:port` (recommended)
- `socks4://host:port`
- `http://host:port`
- `https://host:port`

### Example: SSH Tunnel

Create a SOCKS5 proxy using SSH:

```bash
# Create tunnel to a server in the target region
ssh -D 1080 -N user@french-server.com

# Configure in kiosque.conf:
# [proxy]
# url = socks5://localhost:1080
```

### Geo-Blocked Websites

Known geo-blocked websites that require proxies:

- **Courrier International** - France/Europe only (returns 406)
- **Les Échos** - France/Europe only (returns 403)

See [Troubleshooting Guide](../troubleshooting.md#403-forbidden-or-406-not-acceptable-geo-blocking) for detailed proxy troubleshooting.

## Security Best Practices

### Protecting Your Credentials

- **Never commit** your `kiosque.conf` file to version control (it's in `.gitignore`)
- **Use environment variables** for CI/CD if needed
- **Rotate tokens** periodically for API integrations
- **Limit token scopes** to minimum required permissions

### File Permissions

Ensure your configuration file is only readable by you:

```bash
chmod 600 ~/.config/kiosque/kiosque.conf
```

## Configuration Examples

### Minimal Configuration (Article Extraction Only)

```ini
[https://www.lemonde.fr/]
username = your.email@example.com
password = your_password
```

### Full Configuration (All Features)

```ini
# News websites
[https://www.lemonde.fr/]
username = your.email@example.com
password = your_password

[https://www.nytimes.com/]
cookie_nyt_s = your_nyt_cookie_value

[https://www.theguardian.com/]
username = your.email@example.com
password = your_password

# API integrations
[raindrop.io]
token = your_raindrop_api_token

[github]
token = ghp_your_github_personal_access_token

# Proxy (optional)
[proxy]
url = socks5://localhost:1080
```

## Next Steps

- **Usage Examples:** See [Quick Start Guide](../index.md) for usage examples
- **Website List:** See [Supported Sites](../websites/supported-sites.md) for all supported websites
- **Authentication Details:** See [Authentication Guide](../websites/authentication.md) for site-specific auth instructions
- **Troubleshooting:** See [Troubleshooting Guide](../troubleshooting.md) for common issues
