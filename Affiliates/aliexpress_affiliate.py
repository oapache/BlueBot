"""
aliexpress_affiliate_link_generator.py
--------------------------------------

Automates the generation of AliExpress affiliate links through the official API.

This script:
1. Expands shortened URLs to get the full product link.
2. Extracts the product ID from each URL.
3. Generates authenticated API requests to AliExpress’s affiliate endpoint.
4. Retrieves and returns the generated affiliate links.

Useful for affiliate automation, marketing bots, and large-scale product sharing.

Author: Saullo Gabryel
"""

import requests
import hashlib
import time
import re
from typing import List, Optional

# Global API configuration (to be filled with valid credentials)
url_api = ''
app_key = ''
app_secret = ''
tracking_id = ''


def expandir_link(short_url: str) -> str:
    """
    Expands a shortened AliExpress (or third-party) URL to its final destination.

    Args:
        short_url (str): The shortened URL.

    Returns:
        str: The expanded, final URL.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(short_url, allow_redirects=True, headers=headers, timeout=5)

        print(f"🔍 Final URL: {response.url}")
        print(f"📦 Status code: {response.status_code}")
        print(f"📄 Raw HTML (first 500 chars): {response.text[:500]}...")

        return response.url

    except Exception as e:
        print(f"❌ Error expanding link {short_url}: {type(e).__name__}: {e}")
        return short_url


def extrair_id_do_produto(url: str) -> Optional[str]:
    """
    Extracts the AliExpress product ID from a given URL.

    Args:
        url (str): Full product URL.

    Returns:
        Optional[str]: Product ID if found, otherwise None.
    """
    # Try to extract ID from query parameters
    match = re.search(r'productIds=(\d+)', url)
    if match:
        return match.group(1)

    # Try to extract ID from standard AliExpress URL structure
    match = re.search(r'/item/(\d+)\.html', url)
    if match:
        return match.group(1)

    # Fallback: extract any long numeric sequence (8+ digits)
    match = re.search(r'(\d{8,})', url)
    if match:
        return match.group(1)

    return None


def gerar_links_afiliado_aliexpress(
    links: List[str],
    app_key: str,
    app_secret: str,
    tracking_id: str
) -> List[Optional[str]]:
    """
    Generates affiliate links for multiple AliExpress product URLs using the AliExpress API.

    Args:
        links (List[str]): List of product URLs (shortened or full).
        app_key (str): API app key from AliExpress.
        app_secret (str): API secret key.
        tracking_id (str): Affiliate tracking ID.

    Returns:
        List[Optional[str]]: A list of affiliate URLs or None for failed ones.
    """
    results = []

    def gerar_sign(params: dict, secret: str) -> str:
        """
        Generates the MD5-based signature required by the AliExpress API.

        Args:
            params (dict): API parameters to sign.
            secret (str): App secret key.

        Returns:
            str: Uppercase MD5 hash representing the signature.
        """
        sign_str = secret + ''.join(f"{k}{v}" for k, v in sorted(params.items())) + secret
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()

    # Process each provided link
    for link in links:
        print(f"🔗 Processing link: {link}")

        # Expand shortened URL if necessary
        expanded_link = expandir_link(link)

        # Extract product ID
        product_id = extrair_id_do_produto(expanded_link)
        if product_id:
            product_url = f"https://www.aliexpress.com/item/{product_id}.html"
        else:
            print(f"⚠️ Could not extract product ID from {expanded_link}")
            results.append(None)
            continue

        # Prepare request parameters
        params = {
            "method": "aliexpress.affiliate.link.generate",
            "app_key": app_key,
            "timestamp": int(time.time() * 1000),
            "format": "json",
            "sign_method": "md5",
            "promotion_link_type": "0",
            "source_values": product_url,
            "tracking_id": tracking_id,
        }

        # Generate API signature
        params["sign"] = gerar_sign(params, app_secret)

        try:
            # Make the API call
            response = requests.get(url_api, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                print(f"📝 API Response:\n{data}\n")

                # Drill down into the nested response structure
                result = (
                    data.get("aliexpress_affiliate_link_generate_response", {})
                    .get("resp_result", {})
                    .get("result", {})
                )

                promotion_links = result.get("promotion_links", {})
                promotion_link_list = promotion_links.get("promotion_link", [])

                # Extract the first valid affiliate link
                if promotion_link_list:
                    affiliate_link = promotion_link_list[0].get("promotion_link")
                    results.append(affiliate_link)
                    print(f"✅ Affiliate link generated: {affiliate_link}")
                else:
                    print(f"⚠️ API returned no promotion_links for: {product_url}")
                    results.append(None)
            else:
                print(f"❌ HTTP {response.status_code} for link: {product_url}")
                results.append(None)

        except Exception as e:
            print(f"❌ Error processing {product_url}: {type(e).__name__}: {e}")
            results.append(None)

    return results
