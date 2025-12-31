# New York Times Cookie Authentication Setup

The New York Times uses CAPTCHA-protected login, making automated authentication difficult. Instead, we use **cookie-based authentication** where you extract your session cookie from your browser after logging in manually.

## Quick Setup (5 minutes)

### Step 1: Log in to NYT

1. Open your browser and go to https://www.nytimes.com
2. Click "Log In" and enter your credentials
3. Make sure you're successfully logged in (you should see your name/account)

### Step 2: Extract the Cookie

#### Chrome / Brave / Edge:

1. Press `F12` to open Developer Tools
2. Click the **Application** tab (or **Storage** in some browsers)
3. In the left sidebar, expand **Cookies** → **https://www.nytimes.com**
4. Find the cookie named **`NYT-S`**
5. Double-click the **Value** column to select the entire cookie value
6. Copy it (Ctrl+C / Cmd+C)

#### Firefox:

1. Press `F12` to open Developer Tools
2. Click the **Storage** tab
3. Expand **Cookies** → **https://www.nytimes.com**
4. Find the cookie named **`NYT-S`**
5. Double-click the **Value** to select and copy

#### Safari:

1. Enable Developer menu: Preferences → Advanced → Show Develop menu
2. Develop → Show Web Inspector
3. Click **Storage** tab
4. Select **Cookies** → **https://www.nytimes.com**
5. Find **`NYT-S`** and copy the value

### Step 3: Add to Kiosque Config

Open your kiosque configuration file:

```bash
# Linux/Mac
nano ~/.config/kiosque/kiosque.conf

# Or use your favorite editor
code ~/.config/kiosque/kiosque.conf
```

Add or update the NYT section:

```ini
[https://www.nytimes.com]
cookie_nyt_s = YOUR_COOKIE_VALUE_HERE
```

**Important:**

- Replace `YOUR_COOKIE_VALUE_HERE` with the actual cookie value you copied
- The cookie value is usually a long string of characters
- Don't add quotes around the value

### Step 4: Test

```bash
kiosque https://www.nytimes.com/2025/12/30/well/social-smoking.html test.md
cat test.md
```

You should now see the **full article** instead of just a preview!

## Troubleshooting

### "Still seeing paywall messages"

1. Make sure you copied the entire cookie value (it's long!)
2. Check there are no extra spaces in the config file
3. Verify you're logged in to NYT in your browser
4. Try logging out and back in, then get a fresh cookie

### "Cookie expired"

NYT cookies typically last several months, but they do expire. When this happens:

1. Log in to nytimes.com again in your browser
2. Extract a new cookie value
3. Update your config file

### "Getting 403 errors"

This means:

- Cookie is invalid or expired
- Cookie wasn't set correctly in config
- Try clearing kiosque cache and getting a fresh cookie

## Security Notes

- **Your NYT cookie is like a password** - don't share it
- The cookie gives access to your NYT subscription
- Anyone with your cookie can access NYT as you
- Store your config file securely (it should be readable only by you)

## Cookie Lifespan

- NYT cookies typically last **3-6 months**
- The cookie may expire sooner if you log out
- You'll need to refresh it occasionally

## Alternative: Username/Password (Not Recommended)

Username/password authentication is not currently supported due to:

- CAPTCHA protection on login page
- Risk of account lockout
- NYT's aggressive bot detection

Cookie-based auth is more reliable and secure.

## How It Works

When you provide the `cookie_nyt_s` value:

1. Kiosque adds the cookie to HTTP requests
2. NYT sees the valid session cookie
3. NYT serves you the full article (as a logged-in subscriber)
4. Kiosque extracts and converts to markdown

This is the same as accessing NYT articles in your browser while logged in.
