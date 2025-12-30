import logging

import httpx
import stamina

from .config import validate_proxy_config

# Initialize client with optional proxy support
proxy_config = validate_proxy_config()
proxy_url = proxy_config.url if proxy_config else None

if proxy_url:
    # For SOCKS proxies, we need to use httpx_socks transport
    if proxy_url.startswith("socks"):
        from httpx_socks import SyncProxyTransport

        transport = SyncProxyTransport.from_url(proxy_url)
        client = httpx.Client(
            follow_redirects=True, timeout=30.0, transport=transport
        )
        logging.info(f"Using SOCKS proxy: {proxy_url}")
    else:
        # For HTTP/HTTPS proxies, httpx handles them natively
        client = httpx.Client(
            follow_redirects=True, timeout=30.0, proxy=proxy_url
        )
        logging.info(f"Using HTTP proxy: {proxy_url}")
else:
    client = httpx.Client(follow_redirects=True, timeout=30.0)

client.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) "
            "Gecko/20100101 Firefox/115.0"
        )
    }
)


# Retry configuration for HTTP requests
# Retries on common transient failures with exponential backoff
@stamina.retry(
    on=httpx.HTTPError,
    attempts=3,
    timeout=None,
)
def get_with_retry(url: str, **kwargs) -> httpx.Response:
    """HTTP GET with automatic retry on transient failures."""
    return client.get(url, **kwargs)


@stamina.retry(
    on=httpx.HTTPError,
    attempts=3,
    timeout=None,
)
def post_with_retry(url: str, **kwargs) -> httpx.Response:
    """HTTP POST with automatic retry on transient failures."""
    return client.post(url, **kwargs)
