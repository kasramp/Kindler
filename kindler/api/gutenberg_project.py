import requests
import logging
from flask import render_template, Blueprint, request

gutenberg_bp = Blueprint("gutenberg", __name__, url_prefix="/gutenberg")

third_party_gutendex_base_url = "https://gutendex.com/books/"
self_hosted_gutendex_base_url = "http://gutendex:9193/books/"


@gutenberg_bp.route("/")
def home():
    return render_template("index_gutenberg.html")


@gutenberg_bp.route("/search")
def search():
    # TODO - support multiple pages
    query = request.args.get("q")
    response = search_book_from_gutendex_api(query)
    books = response.json().get("results", [])
    return render_template("result_gutenberg.html", query=query, results=books)


@gutenberg_bp.route("/readability")
def readability_page():
    query = request.args.get("q")
    book_id = request.args.get("id")
    response = retrieve_book_details_by_id_from_gutendex_api(book_id).json()
    return render_template("read_gutenberg.html", query=query, book=response)


def search_book_from_gutendex_api(query):
    try:
        response = requests.get(
            self_hosted_gutendex_base_url, params={"search": query}, timeout=5
        )
        logging.info(f"Successfully called self-hosted Gutendex for: '{query}' keyword")
        return response
    except (requests.ConnectionError, requests.Timeout):
        logging.info(
            f"Failed to call self-hosted Gutendex for: '{query}' keyword. Trying third-party now"
        )
        return requests.get(
            third_party_gutendex_base_url, params={"search": query}, timeout=5
        )


def retrieve_book_details_by_id_from_gutendex_api(book_id):
    try:
        response = requests.get(f"{self_hosted_gutendex_base_url}{book_id}", timeout=5)
        logging.info(
            f"Successfully called self-hosted Gutendex to retrieve book details of book_id: '{book_id}'"
        )
        return response
    except (requests.ConnectionError, requests.Timeout):
        logging.info(
            f"Failed to call self-hosted Gutendex to retrieve book details of book_id: '{book_id}'. Trying third-party now"
        )
        return requests.get(f"{third_party_gutendex_base_url}{book_id}", timeout=5)
