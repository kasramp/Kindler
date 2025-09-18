import logging

import requests


def is_blob_content(url):
    try:
        head_resp = requests.head(url, allow_redirects=True, timeout=5)
        content_type = head_resp.headers.get("Content-Type", "").lower()
        if content_type and not (
            content_type.startswith("text/html")
            or content_type.startswith("application/xhtml+xml")
        ):
            return True, None
    except requests.RequestException:
        logging.info(f"HEAD request failed for {url}, falling back to GET.")
    req = requests.get(url, timeout=10)
    req.raise_for_status()
    content_type = req.headers.get("Content-Type", "").lower()
    if not (
        content_type.startswith("text/html")
        or content_type.startswith("application/xhtml+xml")
    ):
        return True, req
    return False, req
