import logging

import requests
from requests.exceptions import SSLError

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.google.com/",
    "DNT": "1",
}


def is_blob_content(url):
    verify_cert = True
    try:
        head_resp = requests.head(
            url, allow_redirects=True, timeout=5, verify=verify_cert
        )
        content_type = head_resp.headers.get("Content-Type", "").lower()
        if content_type and not (
            content_type.startswith("text/html")
            or content_type.startswith("application/xhtml+xml")
            or content_type.startswith("text/plain")
        ):
            return True, None
    except SSLError as error:
        logging.info(
            f"Cannot get cert, trying without cert verification. Error: {error}"
        )
        verify_cert = False
    except requests.RequestException as error:
        logging.info(
            f"HEAD request failed for {url}, falling back to GET. Error: {error}"
        )
    req = requests.get(
        url, headers=HEADERS, timeout=10, allow_redirects=True, verify=verify_cert
    )
    req.raise_for_status()
    content_type = req.headers.get("Content-Type", "").lower()
    if not (
        content_type.startswith("text/html")
        or content_type.startswith("application/xhtml+xml")
        or content_type.startswith("text/plain")
    ):
        return True, req
    req = redirect_medium(url, req)
    return False, req


def redirect_medium(url, response):
    if 'content="Medium"' not in response.text:
        return response
    try:
        req = requests.get("https://freedium.cfd/" + url, headers=HEADERS, timeout=10)
        req.raise_for_status()
        return req
    except Exception:
        return response
