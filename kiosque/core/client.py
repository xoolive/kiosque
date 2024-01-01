import httpx

client = httpx.Client()
client.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) "
            "Gecko/20100101 Firefox/115.0"
        )
    }
)
