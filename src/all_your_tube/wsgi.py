"""
WSGI configuration for production deployment.
"""

import subprocess
import sys
from pathlib import Path

from .app import app

# WSGI application object
application = app


def main():
    """Run the application with Gunicorn using configuration file."""

    # Find gunicorn config file relative to this module
    config_path = Path(__file__).parent.parent.parent / "gunicorn.conf.py"

    # Build gunicorn command with config file
    cmd = ["gunicorn", "--config", str(config_path), "all_your_tube.wsgi:application"]

    # Execute gunicorn
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
