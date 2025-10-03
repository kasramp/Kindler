import requests
from flask import render_template, Blueprint, request

gutenberg_bp = Blueprint("gutenberg", __name__, url_prefix="/gutenberg")

HEADERS = {"Host": "localhost"}
base_url = "https://gutendex.com/books/"
local_base_url = "http://gutendex_stack_web:9193/books/"


@gutenberg_bp.route("/")
def home():
    return render_template("index_gutenberg.html")


@gutenberg_bp.route("/search")
def search():
    # TODO - support multiple pages
    query = request.args.get("q")
    is_success, response = is_local_gutendex_accessible(query)
    print(f"Result from local Gutendex is: {is_success}")
    if not is_success or response is None:
        response = requests.get(base_url, params={"search": query})
    books = response.json().get("results", [])
    return render_template("result_gutenberg.html", query=query, results=books)


@gutenberg_bp.route("/readability")
def readability_page():
    query = request.args.get("q")
    book_id = request.args.get("id")
    response = requests.get(f"{base_url}{book_id}").json()
    return render_template("read_gutenberg.html", query=query, book=response)


def is_local_gutendex_accessible(query):
    try:
        response = requests.get(
            local_base_url, params={"search": query}, headers=HEADERS, timeout=10
        )
        return True, response
    except (requests.ConnectionError, requests.Timeout):
        return False, None
