import logging

from flask import render_template, Blueprint, request, redirect, url_for
from googlenewsdecoder import gnewsdecoder
from pygooglenews import GoogleNews

news_bp = Blueprint("news", __name__, url_prefix="/news")


@news_bp.route("/")
def home():
    return render_template("index_news.html")


# Needs caching of news for 1H TTL
@news_bp.route("/search")
def search():
    google_news = GoogleNews()
    category = request.args.get("news-category")
    if "top" == category:
        news = google_news.top_news()
    elif category in ("technology", "business"):
        news = google_news.topic_headlines(category)
    else:
        country_lang = category.split("-")
        google_news = GoogleNews(country=country_lang[0], lang=country_lang[1])
        news = google_news.geo_headlines(country_lang[0])
    return render_template(
        "result_news.html", category=category, results=news["entries"]
    )


# Needs caching of links for 24H TTL
@news_bp.route("/readability")
def readability_page():
    url = decode_google_news_url(request.args.get("url"))
    return redirect(url_for("web.readability_page", url=url, q=""))


def decode_google_news_url(url):
    try:
        decoded_url = gnewsdecoder(url, interval=1)
        if decoded_url.get("status"):
            return decoded_url["decoded_url"]
        else:
            logging.error(f'Error decoding url ${decoded_url["message"]}')
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return url
