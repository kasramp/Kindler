from flask import render_template, Blueprint

front_bp = Blueprint("front", __name__)


@front_bp.route("/front")
def front():
    return render_template("front.html")
