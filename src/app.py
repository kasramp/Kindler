from flask import Flask
from api.home import home_bp
from api.gemini import gemini_bp
from api.news import news_bp

app = Flask(__name__)
app.register_blueprint(home_bp)
app.register_blueprint(gemini_bp)
app.register_blueprint(news_bp)

if __name__ == '__main__':
    app.run(debug=True)