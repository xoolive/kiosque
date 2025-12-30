#!/usr/bin/env python3
"""Test script to verify proxy configuration and connectivity.

Usage:
    python test_proxy.py [proxy_url]

Examples:
    python test_proxy.py socks5://localhost:1080
    python test_proxy.py http://proxy.example.com:8080
"""

import sys

import httpx
from httpx_socks import SyncProxyTransport


def test_proxy(proxy_url: str | None = None):
    """Test proxy connectivity and geo-blocked websites."""
    print("=" * 60)
    print("Kiosque Proxy Test Utility")
    print("=" * 60)

    # Test URLs - geo-blocked websites
    test_sites = {
        "Courrier International": "https://www.courrierinternational.com/",
        "Les Échos": "https://www.lesechos.fr/",
    }

    # If no proxy specified, check config
    if proxy_url is None:
        from kiosque.core.config import validate_proxy_config

        proxy_config = validate_proxy_config()
        if proxy_config:
            proxy_url = proxy_config.url
            print(f"\nUsing proxy from config: {proxy_url}")
        else:
            print("\nNo proxy configured. Testing direct connection...")
            print(
                "To test with proxy, either:\n"
                "  1. Add [proxy] section to ~/.config/kiosque/kiosque.conf\n"
                "  2. Run: python test_proxy.py socks5://localhost:1080"
            )
    else:
        print(f"\nUsing proxy: {proxy_url}")

    print("\n" + "-" * 60)

    # Create client with or without proxy
    if proxy_url:
        if proxy_url.startswith("socks"):
            transport = SyncProxyTransport.from_url(proxy_url)
            client = httpx.Client(
                transport=transport, timeout=30.0, follow_redirects=True
            )
        else:
            client = httpx.Client(
                proxy=proxy_url, timeout=30.0, follow_redirects=True
            )
    else:
        client = httpx.Client(timeout=30.0, follow_redirects=True)

    # Add realistic user agent
    client.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) "
                "Gecko/20100101 Firefox/115.0"
            )
        }
    )

    # Test each website
    for site_name, url in test_sites.items():
        print(f"\nTesting {site_name}:")
        print(f"  URL: {url}")

        try:
            response = client.get(url)
            status = response.status_code

            if status == 200:
                print(f"  ✅ SUCCESS (HTTP {status})")
                print(f"  Content length: {len(response.content)} bytes")

                # Check if we got actual content
                if len(response.content) > 1000:
                    print("  🎉 Website is accessible!")
                else:
                    print(
                        "  ⚠️  Got 200 but content seems small "
                        "(possible blocking)"
                    )

            elif status in (403, 406):
                print(f"  ❌ GEO-BLOCKED (HTTP {status})")
                print("  This website blocks your current location/IP address.")
                if not proxy_url:
                    print("  💡 Try using a proxy in France/Europe")
                else:
                    print("  💡 Proxy might not be in the right region")

            elif status >= 300 and status < 400:
                print(f"  ↪️  REDIRECT (HTTP {status})")
                print(f"  Location: {response.headers.get('location', 'N/A')}")

            else:
                print(f"  ⚠️  UNEXPECTED (HTTP {status})")

        except httpx.ConnectError as e:
            print("  ❌ CONNECTION ERROR")
            print(f"  {e}")
            if proxy_url:
                print("  💡 Check if proxy is running and accessible")

        except httpx.TimeoutException:
            print("  ❌ TIMEOUT")
            print("  Request took too long (>30s)")
            if proxy_url:
                print("  💡 Proxy might be slow or not responding")

        except Exception as e:
            print(f"  ❌ ERROR: {type(e).__name__}")
            print(f"  {e}")

    print("\n" + "=" * 60)
    print("Test complete!")

    if proxy_url:
        print(
            "\n💡 If sites are still blocked with proxy, ensure your proxy "
            "is located in France/Europe."
        )
    else:
        print("\n💡 To test with a proxy, configure it in kiosque.conf or run:")
        print("   python test_proxy.py socks5://localhost:1080")

    client.close()


if __name__ == "__main__":
    proxy = sys.argv[1] if len(sys.argv) > 1 else None
    test_proxy(proxy)
