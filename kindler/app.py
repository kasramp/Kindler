from flask import Flask
from kindler.api.home import home_bp
from kindler.api.gemini import gemini_bp
from kindler.api.news import news_bp
from kindler.api.gutenberg_project import gutenberg_bp
from flask_healthz import healthz

app = Flask(__name__)
app.register_blueprint(home_bp)
app.register_blueprint(gemini_bp)
app.register_blueprint(news_bp)
app.register_blueprint(gutenberg_bp)
app.register_blueprint(healthz, url_prefix="/healthz")


def liveness():
    return True, {"status": "up"}


def readiness():
    return True, {"status": "up"}


app.config.update(HEALTHZ={"live": liveness, "ready": readiness})

if __name__ == "__main__":
    app.run(debug=True)
