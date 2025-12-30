import httpx
import stamina

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
