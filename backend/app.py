"""
app.py — Flask entry point
"""

from flask import Flask
from flask_cors import CORS
from routes.proxy import proxy_bp
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Fix CORS — allow all origins (frontend on any port)
CORS(app, resources={r"/api/*": {"origins": "*"}})

app.register_blueprint(proxy_bp, url_prefix="/api")


@app.route("/", methods=["GET"])
def health():
    return {"status": "ok", "message": "PHI Redaction Proxy is running"}, 200


if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
