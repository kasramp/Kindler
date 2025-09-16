import requests
from flask import render_template, Blueprint, request

from kindler.search import FuzzySearcher

gutenberg_au_bp = Blueprint("gutenberg_au", __name__, url_prefix="/gutenberg_au")

searcher = FuzzySearcher()


@gutenberg_au_bp.route("/")
def home():
    return render_template("index_gutenberg_au.html")


@gutenberg_au_bp.route("/search")
def search():
    # TODO - support multiple pages
    query = request.args.get("q")
    books = searcher.search(query)
    return render_template("result_gutenberg_au.html", query=query, results=books)


## Implement pulling and proper rendering of the content
# @gutenberg_au_bp.route("/readability")
# def readability_page():
#     query = request.args.get("q")
#     book_id = request.args.get("id")
#     response = requests.get(f"{base_url}{book_id}").json()
#     return render_template("read_gutenberg.html", query=query, book=response)
