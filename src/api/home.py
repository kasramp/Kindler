import io
import logging
from urllib.parse import urljoin, urlparse, quote

import aspose.words as aw
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from flask import render_template, Blueprint, request, Response, send_file
from readabilipy import simple_json_from_html_string

home_bp = Blueprint('home', __name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.google.com/',
    'DNT': '1',
}


@home_bp.route('/')
def home():
    return render_template('index.html')


@home_bp.route('/search')
def search():
    query = request.args.get('q')
    if not query:
        logging.warning("Search query is empty.")
        return "Please provide a search query.", 400
    results = DDGS().text(query, max_results=100, backend="duckduckgo")
    return render_template('result.html', query=query, results=results)


@home_bp.route("/readability")
def readability_page():
    url = request.args.get('url')
    if not url:
        logging.warning("Readability URL is empty.")
        return "Please provide a URL to clean.", 400
    try:
        req = requests.get(url, headers=HEADERS, timeout=10)
        req.raise_for_status()
        article = simple_json_from_html_string(req.text, use_readability=True)
        return render_template('read.html', title=article['title'],
                               content=clean_readability_html(article['content'], url), url=url)

    except requests.exceptions.RequestException as e:
        logging.error(f"Network error fetching URL: {e}")
        return f"A network error occurred: {e}", 500
    except Exception as e:
        logging.error(f"An error occurred during readability processing: {e}")
        return f"An error occurred during processing: {e}", 500


@home_bp.route("/save_page")
def save_page():
    url = request.args.get('url')
    save_format = request.args.get('format', 'html')
    if not url:
        return "No URL provided", 400
    req = requests.get(url, headers=HEADERS, timeout=10)
    article = simple_json_from_html_string(req.text, use_readability=True)
    html_content = render_template(
        'read_save_formatted.html',
        title=article['title'],
        content=clean_readability_html(article['content'], url),
        url=url
    )
    doc = aw.Document()
    builder = aw.DocumentBuilder(doc)
    builder.insert_html(html_content)
    if "html" == save_format:
        response = Response(html_content, mimetype="text/html")
        response.headers["Content-Disposition"] = f"attachment; filename={article['title']}.html"
        return response
    else:
        buffer = io.BytesIO()
        # doc.save(buffer, aw.SaveFormat.MOBI) -> .MOBI in dynamic formatting
        doc.save(buffer, getattr(aw.SaveFormat, save_format.upper()))
        buffer.seek(0)
        file_name = f'{article['title']}.{save_format}'
        return send_file(buffer, as_attachment=True, download_name=file_name)


def clean_readability_html(html_content, base_url):
    soup = BeautifulSoup(html_content, 'html.parser')

    # --- Remove unhelpful tags (media, scripts, forms, etc.) ---
    for tag in soup.find_all([
        'img', 'picture', 'source', 'figure',
        'script', 'style', 'iframe', 'form',
        'button', 'noscript', 'svg', 'video', 'audio'
    ]):
        tag.decompose()

    # --- Drop navigation/menus explicitly ---
    for nav in soup.find_all('nav'):
        nav.decompose()
    for div in soup.find_all('div', class_=lambda c: c and 'nav' in c.lower()):
        div.decompose()
    for ul in soup.find_all('ul', class_=lambda c: c and ('menu' in c.lower() or 'nav' in c.lower())):
        ul.decompose()
    for ol in soup.find_all('ol', class_=lambda c: c and ('menu' in c.lower() or 'nav' in c.lower())):
        ol.decompose()

    # --- Rewrite links to go through /readability ---
    readability_endpoint = '/readability?url='
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith("#"):
            # Remove back-to-top style anchors
            link.decompose()
            continue
        absolute_url = urljoin(base_url, href)
        if urlparse(absolute_url).scheme not in ('http', 'https'):
            continue
        encoded = quote(absolute_url, safe='')
        link['href'] = f"{readability_endpoint}{encoded}"

    # --- Strip attributes (keep only essential ones) ---
    for tag in soup.find_all(True):
        allowed_attrs = {'a': ['href', 'id', 'name'], 'sup': ['id']}
        tag.attrs = {k: v for k, v in tag.attrs.items() if k in allowed_attrs.get(tag.name, [])}

    # --- Whitelist allowed tags ---
    allowed_tags = [
        'p', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'pre', 'br', 'sup', 'sub', 'strong', 'em', 'ul', 'ol', 'li'
    ]
    for tag in soup.find_all(True):
        if tag.name not in allowed_tags:
            tag.unwrap()

    # --- Remove empty paragraphs ---
    for p in soup.find_all('p'):
        if not p.get_text(strip=True):
            p.decompose()

    # --- Return cleaned HTML ---
    return "\n".join(line.strip() for line in str(soup).splitlines() if line.strip())
