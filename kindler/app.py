from flask import Flask, redirect, url_for
from flask_healthz import healthz

from kindler.api.error import error_bp
from kindler.api.gemini import gemini_bp
from kindler.api.gutenberg_project import gutenberg_bp
from kindler.api.home import home_bp
from kindler.api.news import news_bp
from kindler.api.web import web_bp

app = Flask(__name__)
app.register_blueprint(web_bp)
app.register_blueprint(gemini_bp)
app.register_blueprint(news_bp)
app.register_blueprint(gutenberg_bp)
app.register_blueprint(home_bp)
app.register_blueprint(error_bp)
app.register_blueprint(healthz, url_prefix="/healthz")


def liveness():
    return True, {"status": "up"}


def readiness():
    return True, {"status": "up"}


app.config.update(HEALTHZ={"live": liveness, "ready": readiness})


@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for("error.error", status_code=404))


if __name__ == "__main__":
    app.run(debug=True)
