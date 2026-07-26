#!/usr/bin/env python3
"""
WSGI entry point for Kiselgram production deployment.
Run with: gunicorn wsgi:app
"""

import os
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from werkzeug.middleware.proxy_fix import ProxyFix

app = create_app()
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

if __name__ == "__main__":
    app.run(port=5600)