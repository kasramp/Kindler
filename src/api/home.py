import requests
from flask import render_template, Blueprint
from readabilipy import simple_json_from_html_string

home_bp = Blueprint('home', __name__)


@home_bp.route('/')
def home():
    req = requests.get('https://www.geekyhacker.com/execute-commands-as-the-root-user-on-openbsd-with-doas/')
    article = simple_json_from_html_string(req.text, use_readability=True)
    return render_template('index.html',
                           content=article['plain_content'],
                           title=article['title'])
