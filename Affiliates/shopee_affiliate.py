"""
shopee_affiliate_link_generator.py
----------------------------------

Automates the generation of Shopee affiliate links.

This script:
1. Expands shortened Shopee URLs to their final destination.
2. Cleans old affiliate parameters and injects new tracking parameters.
3. Optionally shortens the final affiliate URL using TinyURL or is.gd.
4. Returns a ready-to-use Shopee affiliate link.

Author: Saullo Gabryel
"""

import httpx
import random
import string
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode


async def expand_shopee_url(url: str) -> str:
    """
    Expands a Shopee shortened URL to its final destination URL.

    Args:
        url (str): The shortened Shopee URL.

    Returns:
        str: The fully expanded URL after following redirects.
    """
    async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
        resp = await client.get(url)
        return str(resp.url)  # Final URL after redirects


def clean_and_inject_params(url: str) -> str:
    """
    Removes old affiliate/tracking parameters from a Shopee URL and injects new ones.

    Args:
        url (str): Original or expanded Shopee URL.

    Returns:
        str: URL updated with new affiliate parameters.
    """
    parsed = urlparse(url)
    base_url = parsed._replace(query="").geturl()

    # Remove existing affiliate/tracking parameters
    query_params = dict(
        (k, v) for k, v in parse_qsl(parsed.query)
        if not (k.startswith("utm_") or k.startswith("uls_") or
                "track" in k or "affiliate" in k or "ref" in k)
    )

    # Generate new custom tracking parameters
    tracking_id = "bluebot" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    campaign_id = "id_BlueBot" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    term_id = "bot" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

    query_params.update({
        "uls_trackid": tracking_id,
        "utm_campaign": campaign_id,
        "utm_content": "----",
        "utm_medium": "affiliates",
        "utm_source": "",  # Affiliate ID
        "utm_term": term_id,
    })

    # Rebuild the URL with new query parameters
    final_url = base_url + "?" + urlencode(query_params)
    return final_url


async def shorten_url(long_url: str) -> str:
    """
    Attempts to shorten a URL using TinyURL or is.gd services.

    Args:
        long_url (str): Full URL to shorten.

    Returns:
        str: Shortened URL if successful, otherwise returns original URL.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        # Try TinyURL first
        tinyurl_resp = await client.post(
            "https://tinyurl.com/api-create.php",
            params={"url": long_url}
        )
        if tinyurl_resp.status_code == 200 and tinyurl_resp.text.startswith("http"):
            return tinyurl_resp.text

        # Fallback to is.gd
        isgd_resp = await client.post(
            "https://is.gd/create.php",
            params={"format": "simple", "url": long_url}
        )
        if isgd_resp.status_code == 200 and isgd_resp.text.startswith("http"):
            return isgd_resp.text

    # If all fails, return original URL
    return long_url


async def gerar_link_afiliado_shopee(original_link: str) -> str:
    """
    Generates a fully functional Shopee affiliate link.

    Workflow:
    1. Expands shortened URLs if necessary.
    2. Cleans old affiliate parameters and injects new tracking parameters.
    3. Optionally shortens the resulting URL.

    Args:
        original_link (str): Original Shopee link (shortened or full).

    Returns:
        str: Ready-to-use Shopee affiliate link.
    """
    # Determine if the URL is already expanded
    if "shopee.com.br/" in original_link and not original_link.startswith("https://s.shopee.com.br"):
        expanded_url = original_link
    else:
        print("🔗 Expanding Shopee short URL...")
        expanded_url = await expand_shopee_url(original_link)
        print(f"✅ Expanded URL: {expanded_url}")

    # Inject affiliate/tracking parameters
    url_with_params = clean_and_inject_params(expanded_url)
    print(f"🔧 URL with affiliate parameters: {url_with_params}")

    # Shorten the final URL
    shortened_url = await shorten_url(url_with_params)
    print(f"✅ Final shortened URL: {shortened_url}")

    return shortened_url
