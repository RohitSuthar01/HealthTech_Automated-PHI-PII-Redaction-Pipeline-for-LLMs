"""
app.py — Flask entry point
"""

import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from logger import setup_logging
from routes.proxy import proxy_bp

# Initialize structured JSON logging
setup_logging()

load_dotenv()

# Serve static frontend files directly from Flask to completely avoid CORS issues
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))
app = Flask(__name__, static_folder=static_dir, static_url_path="")

# CORS support for development API clients
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Register blueprints
app.register_blueprint(proxy_bp, url_prefix="/api")


@app.route("/", methods=["GET"])
def index():
    """Serve the modular index.html entry point."""
    return app.send_static_file("index.html")


@app.route("/health", methods=["GET"])
def health():
    """Service health check."""
    return {"status": "ok", "message": "PHI Redaction Proxy is running"}, 200


if __name__ == "__main__":
    # In production, this can be served by gunicorn/uwsgi
    app.run(debug=True, port=5001, host="0.0.0.0")
