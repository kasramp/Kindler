import requests
from flask import render_template, Blueprint, request

standard_ebooks_bp = Blueprint(
    "standard_ebooks", __name__, url_prefix="/standard_ebooks"
)

metasearch_url = "http://metasearch:8080/v1/books"
provider = "STANDARD_EBOOKS"


@standard_ebooks_bp.route("/")
def home():
    return render_template("index_standard_ebooks.html")


@standard_ebooks_bp.route("/search")
def search():
    # TODO - support multiple pages
    query = request.args.get("q")
    response = search_book_from_metasearch_api(query)
    books = response.json()
    return render_template("result_standard_ebooks.html", query=query, results=books)


@standard_ebooks_bp.route("/readability")
def readability_page():
    query = request.args.get("q")
    book_id = request.args.get("id")
    response = retrieve_book_details_by_id_from_metasearch_api(book_id).json()
    return render_template("read_standard_ebooks.html", query=query, book=response)


def search_book_from_metasearch_api(query):
    response = requests.get(
        f"{metasearch_url}/search", params={"q": query, "provider": provider}, timeout=5
    )
    return response


def retrieve_book_details_by_id_from_metasearch_api(book_id):
    response = requests.get(f"{metasearch_url}/{book_id}", timeout=5)
    return response
