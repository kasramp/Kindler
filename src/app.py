from flask import Flask
from api.home import home_bp
from api.gemini import gemini_bp

app = Flask(__name__)
app.register_blueprint(home_bp)
app.register_blueprint(gemini_bp)

if __name__ == '__main__':
    app.run(debug=True)