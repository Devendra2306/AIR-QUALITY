"""
WSGI Application Entrypoint for Production Web Deployment (Render / Cloud / PaaS)
Exposes the underlying Flask WSGI server instance for Gunicorn / Uvicorn.
"""

import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from app.dashboard.app import app

# Underlying WSGI Flask instance used by Gunicorn
server = app.server
application = server

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)
