# Troubleshooting Guide

Common issues and solutions for Kiosque.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Configuration Issues](#configuration-issues)
3. [Authentication Issues](#authentication-issues)
4. [Article Extraction Issues](#article-extraction-issues)
5. [TUI Issues](#tui-issues)
6. [Network Issues](#network-issues)
7. [Platform-Specific Issues](#platform-specific-issues)

## Installation Issues

### `command not found: kiosque`

**Problem:** After installing, the `kiosque` command is not available.

**Solutions:**

1. **Check installation method:**

   ```bash
   # If installed with pip:
   pip show kiosque

   # If installed with uv:
   uv run kiosque  # Run directly
   ```

2. **Verify PATH:**

   ```bash
   # pip installs to user directory, check it's in PATH:
   python -m site --user-base
   # Add <output>/bin to your PATH
   ```

3. **Use Python module syntax:**
   ```bash
   python -m kiosque
   ```

### `ModuleNotFoundError: No module named 'kiosque'`

**Problem:** Python can't find the kiosque module.

**Solutions:**

1. **Verify installation:**

   ```bash
   pip list | grep kiosque
   ```

2. **Check Python version:**

   ```bash
   python --version  # Must be 3.12+
   ```

3. **Reinstall:**
   ```bash
   pip uninstall kiosque
   pip install kiosque
   ```

### `pandoc: command not found`

**Problem:** Pandoc is not installed (required for HTML to Markdown conversion).

**Solutions:**

**macOS:**

```bash
brew install pandoc
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt-get install pandoc
```

**Linux (Fedora):**

```bash
sudo dnf install pandoc
```

**Windows:**

```bash
choco install pandoc
```

**Or download from:** https://pandoc.org/installing.html

## Configuration Issues

### "Configuration file not found"

**Problem:** Kiosque can't find the configuration file.

**Solutions:**

1. **Find config location:**

   ```bash
   python -c "from kiosque.core.config import configuration_file; print(configuration_file)"
   ```

2. **Create configuration directory:**

   ```bash
   mkdir -p ~/.config/kiosque
   ```

3. **Create configuration file:**

   ```bash
   cat > ~/.config/kiosque/kiosque.conf << 'EOF'
   [https://www.example.com/]
   username = your_username
   password = your_password

   [raindrop.io]
   token = your_raindrop_token
   EOF
   ```

4. **Custom location via environment variable:**
   ```bash
   export XDG_CONFIG_HOME=/custom/path
   kiosque
   ```

### "Invalid configuration format"

**Problem:** Configuration file has syntax errors.

**Solutions:**

1. **Check INI format:**

   ```ini
   # Good ✓
   [https://www.lemonde.fr/]
   username = user@example.com
   password = mypassword

   # Bad ✗ (missing section)
   username = user@example.com
   password = mypassword
   ```

2. **Check for typos:**

   - Section names must be URLs with `https://`
   - URL must end with `/`
   - Key names: `username`, `password`, `token` (lowercase)

3. **Validate with Python:**
   ```python
   from kiosque.core.config import config_dict
   print(config_dict)  # Should print dict, not error
   ```

## Authentication Issues

### "Login failed" or "403 Forbidden"

**Problem:** Can't log in to website despite correct credentials.

**Solutions:**

1. **Verify credentials:**

   - Log in manually via browser to confirm they work
   - Check for special characters that need escaping
   - Some sites use email, others use username

2. **Check if login flow changed:**

   ```bash
   # Enable verbose logging to see login details:
   kiosque -v https://website.com/article -
   ```

3. **Known broken logins:**
   See `tests/test_login.py` for list of websites with outdated login flows.

4. **Two-factor authentication:**

   - Kiosque doesn't support 2FA
   - Some sites allow app-specific passwords - try creating one

5. **IP-based restrictions:**
   - Some sites block VPN/proxy connections
   - Try disabling VPN temporarily

### "Invalid username or password"

**Problem:** Credentials rejected by website.

**Solutions:**

1. **Check configuration file syntax:**

   ```ini
   [https://www.example.com/]
   username = user@example.com  # No quotes needed
   password = mypassword123      # No quotes needed
   ```

2. **Verify credentials work in browser:**

   - Try logging in manually
   - Check for password reset requirements
   - Verify subscription is active

3. **Check for special characters:**
   ```ini
   # If password contains special chars:
   password = p@ssw0rd!#123  # Should work as-is
   ```

## Article Extraction Issues

### "Website not supported"

**Problem:** URL is not recognized by Kiosque.

**Solutions:**

1. **Check supported websites:**

   - See `websites.md` for complete list
   - 30+ websites currently supported

2. **URL must match base_url:**

   ```bash
   # Good ✓
   kiosque https://www.lemonde.fr/article/...

   # Bad ✗ (missing www subdomain)
   kiosque https://lemonde.fr/article/...
   ```

3. **Contribute support for new website:**
   - See [CONTRIBUTING.md](CONTRIBUTING.md)
   - Adding a new site is usually straightforward

### "Article content is empty" or "NotImplementedError"

**Problem:** Kiosque can't extract article text.

**Solutions:**

1. **Website changed HTML structure:**

   - This is the most common issue
   - Websites update their design, breaking scrapers
   - Open an issue on GitHub with:
     - Website name
     - Example article URL
     - Error message or empty output

2. **Article requires JavaScript:**

   - Some sites load content dynamically with JS
   - Kiosque only handles static HTML
   - Workaround: Try reading in browser reader mode instead

3. **Paywall blocking content:**
   - Some paywalls hide content in HTML (not just visually)
   - Verify you're logged in (use `-v` flag to check)
   - Some sites may block programmatic access even with credentials

### "Unwanted elements in output"

**Problem:** Ads, navigation, or other junk appears in article text.

**Solutions:**

1. **File an issue with:**

   - Website name
   - Example article URL
   - Description of unwanted elements
   - Screenshot if helpful

2. **Quick fix (for developers):**
   Edit the website's `clean_nodes` in `kiosque/website/<site>.py`:
   ```python
   clean_nodes: ClassVar = [
       "figure",
       ("div", {"class": "unwanted-element"}),
   ]
   ```

## TUI Issues

### "No bookmarks found" in TUI

**Problem:** TUI launches but shows no bookmarks from Raindrop.io.

**Solutions:**

1. **Check Raindrop.io token:**

   ```bash
   # Verify token in config file:
   cat ~/.config/kiosque/kiosque.conf | grep token
   ```

2. **Verify token is valid:**

   - Visit https://app.raindrop.io/settings/integrations
   - Check if token is still active
   - Generate new token if needed

3. **Check for unsorted bookmarks:**

   - TUI only shows **Unsorted** bookmarks
   - Move bookmarks to Unsorted collection in Raindrop.io
   - Or modify code to fetch from different collection

4. **Test API manually:**

   ```python
   from kiosque.api.raindrop import Raindrop

   raindrop = Raindrop(token="your_token")
   items = raindrop.retrieve()
   print(f"Found {len(items)} bookmarks")
   ```

### TUI crashes or freezes

**Problem:** TUI becomes unresponsive or crashes.

**Solutions:**

1. **Check terminal size:**

   - TUI requires minimum terminal size
   - Resize terminal to at least 80x24

2. **Kill and restart:**

   ```bash
   # If frozen, kill with:
   Ctrl+C  # or Ctrl+Z then kill %1

   # Restart:
   kiosque
   ```

3. **Check logs:**

   ```bash
   # Run with verbose logging:
   kiosque -v tui
   ```

4. **Update Textual:**
   ```bash
   pip install --upgrade textual
   ```

### "Modal won't close" or keyboard shortcuts not working

**Problem:** TUI keys don't respond as expected.

**Solutions:**

1. **Verify keybindings:**

   - `Esc` closes modal
   - `q` quits (when not in modal)
   - See README for full keybindings

2. **Terminal compatibility:**

   - Some terminals don't send all keys correctly
   - Try a different terminal (e.g., iTerm2, Alacritty)

3. **Check for key conflicts:**
   - Some terminals intercept keys (e.g., tmux)
   - Try running outside tmux/screen

## Network Issues

### "Connection timeout" or "Network error"

**Problem:** Requests to websites time out.

**Solutions:**

1. **Check internet connection:**

   ```bash
   ping google.com
   ```

2. **Retry logic is automatic:**

   - Kiosque retries 3 times with exponential backoff
   - Wait for all retries to complete (may take 30+ seconds)

3. **Increase timeout (for developers):**
   Edit `kiosque/core/client.py`:

   ```python
   client = httpx.Client(timeout=60.0)  # Increase from 30.0
   ```

4. **Check firewall/proxy:**
   - Some corporate networks block certain sites
   - Try from different network

### "SSL certificate verification failed"

**Problem:** HTTPS requests fail due to SSL errors.

**Solutions:**

1. **Update CA certificates:**

   ```bash
   # macOS:
   brew update && brew upgrade openssl

   # Ubuntu:
   sudo apt-get update && sudo apt-get upgrade ca-certificates
   ```

2. **Temporary workaround (not recommended):**
   ```bash
   export CURL_CA_BUNDLE=""
   kiosque https://example.com/article
   ```

### "Too many requests" or "Rate limited"

**Problem:** Website blocks requests due to rate limiting.

**Solutions:**

1. **Wait before retrying:**

   - Most rate limits reset after 15 minutes - 1 hour

2. **Slow down requests:**
   - Don't download many articles rapidly
   - Add delays between downloads

### "403 Forbidden" or "406 Not Acceptable" - Geo-blocking

**Problem:** Website blocks access from your geographic location.

**Known geo-blocked websites:**

- **Courrier International** - Returns 406 outside France/Europe
- **Les Échos** - Returns 403 (Akamai CDN) outside France/Europe

**Solutions:**

1. **Use SOCKS or HTTP proxy:**

   Kiosque supports routing traffic through proxies. Configure in `~/.config/kiosque/kiosque.conf`:

   ```ini
   # Add proxy configuration
   [proxy]
   url = socks5://localhost:1080
   ```

   Supported proxy types:

   - `socks4://host:port` - SOCKS4 proxy
   - `socks5://host:port` - SOCKS5 proxy (recommended)
   - `http://host:port` - HTTP proxy
   - `https://host:port` - HTTPS proxy

   With authentication:

   ```ini
   [proxy]
   url = socks5://username:password@host:port
   ```

2. **Set up SSH tunnel (SOCKS5):**

   If you have SSH access to a server in the target region:

   ```bash
   # Create SOCKS5 proxy on localhost:1080
   ssh -D 1080 -N user@server-in-france.com

   # In another terminal, configure kiosque to use it:
   # Edit ~/.config/kiosque/kiosque.conf and add:
   # [proxy]
   # url = socks5://localhost:1080

   # Then run kiosque normally
   kiosque https://www.courrierinternational.com/article/...
   ```

3. **Use commercial VPN service:**

   Many VPN services offer SOCKS5 proxies:

   - NordVPN: Supports SOCKS5 proxy
   - ExpressVPN: Via manual configuration
   - Shadowsocks: Open-source SOCKS5 solution

   Configure the proxy URL from your VPN provider in kiosque.conf.

4. **Test proxy connection:**

   ```bash
   # Test if proxy works (requires curl with SOCKS support):
   curl --socks5 localhost:1080 https://www.courrierinternational.com/

   # Should return HTML, not 406 error
   ```

5. **Verify proxy in logs:**

   When proxy is configured, you'll see on startup:

   ```
   INFO:root:Using SOCKS proxy: socks5://localhost:1080
   ```

**Note:** Proxy configuration applies to ALL HTTP requests made by Kiosque. To disable, simply remove or comment out the `[proxy]` section in kiosque.conf.

3. **Use browser as fallback:**
   - If blocked, open URL with `o` key in TUI
   - Website may have bot detection

## Platform-Specific Issues

### macOS: "Operation not permitted"

**Problem:** Permission denied errors on macOS.

**Solutions:**

1. **Grant Terminal full disk access:**

   - System Preferences → Security & Privacy → Privacy
   - Full Disk Access → Add Terminal

2. **Fix config directory permissions:**
   ```bash
   chmod 755 ~/.config
   chmod 755 ~/.config/kiosque
   chmod 644 ~/.config/kiosque/kiosque.conf
   ```

### Linux: "Permission denied" writing files

**Problem:** Can't save downloaded articles.

**Solutions:**

1. **Check file permissions:**

   ```bash
   ls -la ~/output.md
   ```

2. **Specify output location:**

   ```bash
   kiosque https://example.com/article ~/Downloads/article.md
   ```

3. **Fix ownership:**
   ```bash
   sudo chown $USER:$USER ~/output.md
   ```

### Windows: "FileNotFoundError" or path issues

**Problem:** File paths not working on Windows.

**Solutions:**

1. **Use forward slashes or raw strings:**

   ```python
   # Good ✓
   path = "C:/Users/Name/article.md"
   path = r"C:\Users\Name\article.md"

   # Bad ✗
   path = "C:\Users\Name\article.md"  # \U escapes
   ```

2. **Check config file location:**

   ```bash
   # Windows config location:
   %APPDATA%\kiosque\kiosque.conf
   # Usually: C:\Users\YourName\AppData\Roaming\kiosque\kiosque.conf
   ```

3. **Use Windows paths in config:**
   ```ini
   # Use forward slashes:
   output_dir = C:/Users/Name/Downloads
   ```

## Still Having Issues?

### Before Opening an Issue

1. **Update to latest version:**

   ```bash
   pip install --upgrade kiosque
   ```

2. **Check existing issues:**

   - https://github.com/yourusername/kiosque/issues

3. **Gather debug information:**

   ```bash
   # Run with verbose logging:
   kiosque -v https://website.com/article - 2>&1 | tee debug.log

   # Include in issue:
   # - Python version: python --version
   # - Kiosque version: pip show kiosque
   # - OS: uname -a (Linux/Mac) or ver (Windows)
   # - Error message or debug.log
   # - Steps to reproduce
   ```

### Open an Issue

Include:

- Description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- Python version, OS, kiosque version
- Relevant logs (with `-v` flag)
- Example article URL (if applicable)

### Get Help

- **GitHub Issues:** Bug reports and feature requests
- **GitHub Discussions:** Questions and community support
- **Documentation:**
  - [README.md](readme.md) - Quick start
  - [ARCHITECTURE.md](ARCHITECTURE.md) - System design
  - [CONTRIBUTING.md](CONTRIBUTING.md) - Development guide

## Common Error Messages Reference

| Error Message                    | Likely Cause              | Solution                               |
| -------------------------------- | ------------------------- | -------------------------------------- |
| `Website not supported`          | URL not in supported list | Check `websites.md` or add support     |
| `NotImplementedError: article()` | Website HTML changed      | Open issue with example URL            |
| `ConnectionError`                | Network issue             | Check internet, retry                  |
| `HTTPStatusError: 403`           | Blocked or login failed   | Check credentials, verify subscription |
| `HTTPStatusError: 404`           | Invalid URL               | Verify URL is correct                  |
| `HTTPStatusError: 429`           | Rate limited              | Wait 15-60 min before retry            |
| `ModuleNotFoundError`            | Installation issue        | Reinstall kiosque                      |
| `FileNotFoundError: pandoc`      | Pandoc not installed      | Install pandoc                         |
| `ValidationError`                | Config file invalid       | Check INI syntax                       |
| `AttributeError: 'NoneType'`     | Article element not found | Website HTML changed, open issue       |

## Debug Mode

Enable maximum verbosity for troubleshooting:

```bash
# CLI:
kiosque -v https://website.com/article -

# Python:
import logging
logging.basicConfig(level=logging.DEBUG)

from kiosque import Website
website = Website.instance("https://website.com/article")
website.save("https://website.com/article", "test.md")
```

This will show:

- HTTP requests and responses
- Login flow details
- HTML parsing steps
- Errors with stack traces
