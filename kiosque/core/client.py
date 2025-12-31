import logging

import httpx
import stamina

from .config import validate_proxy_config

# Initialize client with optional proxy support
proxy_config = validate_proxy_config()
proxy_url = proxy_config.url if proxy_config else None

# TODO: Async client infrastructure available for future async implementations
# Currently, TUI uses asyncio.to_thread() to run sync methods in thread pool
# This async client can be used when refactoring website scrapers to async
if proxy_url:
    # For SOCKS proxies, we need to use httpx_socks transport
    if proxy_url.startswith("socks"):
        from httpx_socks import AsyncProxyTransport, SyncProxyTransport

        transport = SyncProxyTransport.from_url(proxy_url)
        async_transport = AsyncProxyTransport.from_url(proxy_url)
        client = httpx.Client(
            follow_redirects=True, timeout=30.0, transport=transport
        )
        async_client = httpx.AsyncClient(
            follow_redirects=True, timeout=30.0, transport=async_transport
        )
        logging.info(f"Using SOCKS proxy: {proxy_url}")
    else:
        # For HTTP/HTTPS proxies, httpx handles them natively
        client = httpx.Client(
            follow_redirects=True, timeout=30.0, proxy=proxy_url
        )
        async_client = httpx.AsyncClient(
            follow_redirects=True, timeout=30.0, proxy=proxy_url
        )
        logging.info(f"Using HTTP proxy: {proxy_url}")
else:
    client = httpx.Client(follow_redirects=True, timeout=30.0)
    async_client = httpx.AsyncClient(follow_redirects=True, timeout=30.0)

client.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8,"
            "application/signed-exchange;v=b3;q=0.7"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
)

async_client.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8,"
            "application/signed-exchange;v=b3;q=0.7"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
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


# TODO: Async HTTP methods for future use
# These are ready for when website scrapers are refactored to be fully async
# Currently unused - TUI runs sync methods via asyncio.to_thread()
@stamina.retry(
    on=httpx.HTTPError,
    attempts=3,
    timeout=None,
)
async def async_get_with_retry(url: str, **kwargs) -> httpx.Response:
    """Async HTTP GET with automatic retry on transient failures.

    TODO: Use this when refactoring website scrapers to async.
    """
    return await async_client.get(url, **kwargs)


@stamina.retry(
    on=httpx.HTTPError,
    attempts=3,
    timeout=None,
)
async def async_post_with_retry(url: str, **kwargs) -> httpx.Response:
    """Async HTTP POST with automatic retry on transient failures.

    TODO: Use this when refactoring website scrapers to async.
    """
    return await async_client.post(url, **kwargs)
