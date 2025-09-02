from flask import Flask
from kindler.api.home import home_bp
from kindler.api.gemini import gemini_bp
from kindler.api.news import news_bp
from kindler.api.gutenberg_project import gutenberg_bp

app = Flask(__name__)
app.register_blueprint(home_bp)
app.register_blueprint(gemini_bp)
app.register_blueprint(news_bp)
app.register_blueprint(gutenberg_bp)

if __name__ == "__main__":
    app.run(debug=True)
