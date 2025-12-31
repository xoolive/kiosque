# Website Authentication

This guide explains how to configure authentication for paywalled news websites in Kiosque.

## Overview

Many news websites require a subscription to access full articles. Kiosque supports authentication for 20+ paywalled sites, allowing you to extract articles if you have a valid subscription.

## Configuration File

All authentication credentials are stored in `~/.config/kiosque/kiosque.conf` using INI format.

### Finding Your Config File

```bash
# View configuration file location
python -c "from kiosque.core.config import configuration_file; print(configuration_file)"
```

**Default locations:**

- Linux: `~/.config/kiosque/kiosque.conf`
- macOS: `~/.config/kiosque/kiosque.conf`
- Windows: `%APPDATA%\kiosque\kiosque.conf`

## Authentication Methods

### 1. Username/Password (Most Common)

Most websites use standard login forms:

```ini
[https://www.lemonde.fr/]
username = your.email@example.com
password = your_password
```

**Supported sites:**

- Le Monde
- Le Monde Diplomatique
- Courrier International
- Les Échos
- Mediapart
- And many more (see [Supported Sites](supported-sites.md))

### 2. Cookie-Based (NYT, Advanced)

Some sites use anti-bot protection that prevents automated login. For these, extract cookies from your browser:

```ini
[https://www.nytimes.com/]
cookie_nyt_s = your_cookie_value_here
```

**See:** [NYT Cookie Setup Guide](nyt-cookie-setup.md) for detailed instructions.

### 3. API Tokens (Integrations)

For bookmark management integrations:

```ini
[raindrop.io]
token = your_raindrop_api_token

[github]
token = ghp_your_github_personal_access_token
```

**See:**

- [Raindrop.io Integration](../integrations/raindrop.md)
- [GitHub Stars Integration](../integrations/github.md)

## Complete Example

Here's a full configuration with multiple sites:

```ini
# French news sites
[https://www.lemonde.fr/]
username = your.email@example.com
password = your_password

[https://www.lefigaro.fr/]
username = your.email@example.com
password = your_password

# English news sites
[https://www.nytimes.com/]
cookie_nyt_s = very_long_cookie_value_here

[https://www.ft.com/]
username = your.email@example.com
password = your_password

# Integrations (optional)
[raindrop.io]
token = test_token_abc123

[github]
token = ghp_abc123def456
```

## Testing Authentication

Test your credentials with verbose logging to see the login flow:

```bash
# Test with verbose output
kiosque -v https://www.lemonde.fr/article output.md

# You should see:
# INFO: Attempting login to https://www.lemonde.fr/
# INFO: Login successful
# INFO: Extracting article...
```

## Troubleshooting

### Login fails with 403/401 errors

1. **Check credentials** - Verify username/password are correct
2. **Test in browser** - Ensure you can log in manually at the website
3. **Check subscription** - Verify your subscription is active
4. **Verbose mode** - Run with `-v` flag to see detailed login flow

```bash
kiosque -vv https://www.lemonde.fr/article test.md
```

### "Cookie expired" (NYT)

NYT cookies typically last 3-6 months. When expired:

1. Log in to nytimes.com in your browser
2. Extract a new cookie value
3. Update your config file

See [NYT Cookie Setup](nyt-cookie-setup.md) for details.

### Geo-blocking issues

Some sites are only accessible from specific regions:

- **Courrier International** - France/Europe only
- **Les Échos** - France/Europe only

**Solution:** Use a proxy or VPN. See [Troubleshooting](../troubleshooting.md) for proxy configuration.

### CAPTCHA protection

Some sites use CAPTCHA to prevent automated access. Solutions:

1. **Cookie-based auth** - Extract cookies after manual login (like NYT)
2. **Manual CAPTCHA** - Some sites may require occasional manual login
3. **Report issue** - Open a GitHub issue if a previously working site breaks

## Security Best Practices

### Protect Your Credentials

- **File permissions** - Config file should be readable only by you:
  ```bash
  chmod 600 ~/.config/kiosque/kiosque.conf
  ```
- **Never commit** - `.gitignore` includes `kiosque.conf` by default
- **Separate passwords** - Consider using unique passwords for each site
- **Password managers** - Store credentials securely

### What Gets Sent

When you use Kiosque with authentication:

1. **Login request** - Credentials sent via HTTPS to the website's login endpoint
2. **Session cookies** - Stored temporarily in memory
3. **Article requests** - Made with authenticated session
4. **No tracking** - Kiosque doesn't send data anywhere except the target website

Kiosque uses the same HTTPS connections as your web browser.

## Advanced Configuration

### Aliases

Create shortcuts for frequently accessed sites:

```ini
[https://www.lemonde.fr/]
username = your@email.com
password = your_password
alias = lm, monde
```

Use with:

```bash
kiosque lm  # Downloads latest issue
```

### Proxies

Route traffic through a proxy (for geo-blocked sites):

```ini
[proxy]
url = socks5://localhost:1080
```

Supported formats: `socks5://`, `socks4://`, `http://`, `https://`

See [Troubleshooting](../troubleshooting.md) for proxy setup.

## Getting Help

If you have issues with authentication:

1. Check the [Troubleshooting Guide](../troubleshooting.md)
2. Search [GitHub Issues](https://github.com/xoolive/kiosque/issues)
3. Open a new issue with:
   - Website name
   - Error messages (with `-v` verbose flag)
   - Steps you've tried

## See Also

- [NYT Cookie Setup Guide](nyt-cookie-setup.md) - New York Times authentication
- [Supported Sites](supported-sites.md) - Complete list of websites
- [Configuration Guide](../getting-started/configuration.md) - Full configuration reference
- [Troubleshooting](../troubleshooting.md) - Common issues and solutions
