import logging
import os
import subprocess
import tempfile
from urllib.parse import urljoin, urlparse, quote

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from flask import render_template, Blueprint, request, Response
from flask import send_file, abort
from pathvalidate import sanitize_filename
from readabilipy import simple_json_from_html_string

home_bp = Blueprint("home", __name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.google.com/",
    "DNT": "1",
}

allowed_formats = {"html", "epub", "mobi", "azw3"}


@home_bp.route("/")
def home():
    return render_template("index.html")


@home_bp.route("/search")
def search():
    query = request.args.get("q")
    if not query:
        logging.warning("Search query is empty.")
        return "Please provide a search query.", 400
    results = DDGS().text(query, max_results=100, backend="duckduckgo")
    return render_template("result.html", query=query, results=results)


@home_bp.route("/readability")
def readability_page():
    query = request.args.get("q")
    url = request.args.get("url")
    if not url:
        logging.warning("Readability URL is empty.")
        return "Please provide a URL to clean.", 400
    try:
        req = requests.get(url, headers=HEADERS, timeout=10)
        req.raise_for_status()
        article = simple_json_from_html_string(req.text, use_readability=True)
        return render_template(
            "read.html",
            title=article["title"],
            query=query,
            content=clean_readability_html(article["content"], url, query),
            url=url,
        )

    except requests.exceptions.RequestException as e:
        logging.error(f"Network error fetching URL: {e}")
        return f"A network error occurred: {e}", 500
    except Exception as e:
        logging.error(f"An error occurred during readability processing: {e}")
        return f"An error occurred during processing: {e}", 500


@home_bp.route("/save_page")
def save_page():
    url = request.args.get("url")
    query = request.args.get("q")
    save_format = request.args.get("format", "html")
    if not url:
        return "No URL provided", 400
    if save_format not in allowed_formats:
        abort(400, "Invalid format")

    req = requests.get(url, headers=HEADERS, timeout=10)
    article = simple_json_from_html_string(req.text, use_readability=True)
    html_content = render_template(
        "read_save_formatted.html",
        title=article["title"],
        content=clean_readability_html(article["content"], url, query),
        url=url,
    )
    if "html" == save_format:
        response = Response(html_content, mimetype="text/html")
        response.headers["Content-Disposition"] = (
            f"attachment; filename={sanitize_filename(article['title'] + '.html')}"
        )
        return response
    else:
        with tempfile.NamedTemporaryFile(
            suffix=".html", delete=False, mode="w", encoding="utf-8"
        ) as html_tmp:
            html_tmp.write(html_content)
            input_html_file = html_tmp.name
        with tempfile.NamedTemporaryFile(
            suffix=f".{save_format}", delete=False
        ) as output_tmp:
            output_file = output_tmp.name
        try:
            subprocess.run(
                [
                    "ebook-convert",
                    input_html_file,
                    output_file,
                    "--title",
                    article["title"],
                    "--chapter",
                    "//h1",
                    "--level1-toc",
                    "//h1",
                ],
                check=True,
            )
            download_file_name = sanitize_filename(f"{article['title']}.{save_format}")
            response = send_file(
                output_file, as_attachment=True, download_name=download_file_name
            )

            @response.call_on_close
            def cleanup():
                for f in [input_html_file, output_file]:
                    try:
                        os.remove(f)
                        logging.info(f"File {f} deleted")
                    except OSError:
                        pass

            return response
        except subprocess.CalledProcessError as e:
            os.remove(input_html_file)
            if os.path.exists(output_file):
                os.remove(output_file)
            abort(500, f"Conversion failed: {e}")


def clean_readability_html(html_content, base_url, query):
    soup = BeautifulSoup(html_content, "html.parser")

    # --- Remove unhelpful tags (media, scripts, forms, etc.) ---
    for tag in soup.find_all(
        [
            "img",
            "picture",
            "source",
            "figure",
            "script",
            "style",
            "iframe",
            "form",
            "button",
            "noscript",
            "svg",
            "video",
            "audio",
        ]
    ):
        tag.decompose()

    # --- Drop navigation/menus explicitly ---
    for nav in soup.find_all("nav"):
        nav.decompose()
    for div in soup.find_all("div", class_=lambda c: c and "nav" in c.lower()):
        div.decompose()
    for ul in soup.find_all(
        "ul", class_=lambda c: c and ("menu" in c.lower() or "nav" in c.lower())
    ):
        ul.decompose()
    for ol in soup.find_all(
        "ol", class_=lambda c: c and ("menu" in c.lower() or "nav" in c.lower())
    ):
        ol.decompose()

    # --- Rewrite links to go through /readability ---
    readability_endpoint = f"/readability?q={query}&url="
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.startswith("#"):
            # Remove back-to-top style anchors
            link.decompose()
            continue
        absolute_url = urljoin(base_url, href)
        if urlparse(absolute_url).scheme not in ("http", "https"):
            continue
        encoded = quote(absolute_url, safe="")
        link["href"] = f"{readability_endpoint}{encoded}"

    # --- Strip attributes (keep only essential ones) ---
    for tag in soup.find_all(True):
        allowed_attrs = {"a": ["href", "id", "name"], "sup": ["id"]}
        tag.attrs = {
            k: v for k, v in tag.attrs.items() if k in allowed_attrs.get(tag.name, [])
        }

    # --- Whitelist allowed tags ---
    allowed_tags = [
        "p",
        "a",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "pre",
        "br",
        "sup",
        "sub",
        "strong",
        "em",
        "ul",
        "ol",
        "li",
    ]
    for tag in soup.find_all(True):
        if tag.name not in allowed_tags:
            tag.unwrap()

    # --- Remove empty paragraphs ---
    for p in soup.find_all("p"):
        if not p.get_text(strip=True):
            p.decompose()

    # Find all <ul> and <li> tags in the document.
    empty_tags_to_remove = []

    # Iterate over all <li> tags.
    for li_tag in soup.find_all("li"):
        # Check if the tag's text content, after stripping whitespace, is empty.
        if not li_tag.text.strip():
            empty_tags_to_remove.append(li_tag)

    # Iterate over all <ul> tags.
    for ul_tag in soup.find_all("ul"):
        # Check if the tag's text content, after stripping whitespace, is empty.
        # This will also catch <ul> tags that only contained empty <li> tags.
        if not ul_tag.text.strip():
            empty_tags_to_remove.append(ul_tag)

    # Decompose the tags outside the loop to avoid modifying the list being iterated over.
    for tag in empty_tags_to_remove:
        tag.decompose()

    # --- Return cleaned HTML ---
    return "\n".join(line.strip() for line in str(soup).splitlines() if line.strip())
