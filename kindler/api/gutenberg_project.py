import requests
from flask import render_template, Blueprint, request

gutenberg_bp = Blueprint("gutenberg", __name__, url_prefix="/gutenberg")

base_url = "https://gutendex.com/books/"


@gutenberg_bp.route("/")
def home():
    return render_template("index_gutenberg.html")


@gutenberg_bp.route("/search")
def search():
    # TODO - support multiple pages
    query = request.args.get("q")
    response = requests.get(base_url, params={"search": query})
    books = response.json().get("results", [])
    return render_template("result_gutenberg.html", query=query, results=books)


@gutenberg_bp.route("/readability")
def readability_page():
    query = request.args.get("q")
    book_id = request.args.get("id")
    response = requests.get(f"{base_url}{book_id}").json()
    return render_template("read_gutenberg.html", query=query, book=response)
