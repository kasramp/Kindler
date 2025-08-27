import logging
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from flask import render_template, Blueprint, request
from readabilipy import simple_json_from_html_string

home_bp = Blueprint('home', __name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
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
    results = DDGS().text(query, max_results=100)
    return render_template('result.html', query=query, results=results)

# Case study: https://www.bbc.co.uk/programmes/b006mgyl
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
        return render_template('read.html', title=article['title'], content=modify_links_for_readability(article['content']), url=url)

    except requests.exceptions.RequestException as e:
        logging.error(f"Network error fetching URL: {e}")
        return f"A network error occurred: {e}", 500
    except Exception as e:
        logging.error(f"An error occurred during readability processing: {e}")
        return f"An error occurred during processing: {e}", 500


def modify_links_for_readability(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    readability_endpoint = '/readability?url='
    links = soup.find_all('a')
    for link in links:
        original_href = link.get('href')
        if original_href and original_href != '#' and not urlparse(original_href).scheme in ('mailto', 'tel', 'javascript'):
            encoded_url = quote(original_href, safe='')
            new_href = f"{readability_endpoint}{encoded_url}"
            link['href'] = new_href
            print(f"Changed '{original_href}' to '{new_href}'")
    return str(soup)