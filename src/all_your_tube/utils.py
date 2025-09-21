"""
Utility functions for all-your-tube application.
"""

import os


def validate_input(val):
    """Barest minimum code injection check"""
    if val and ";" in val:
        return False
    return True


def get_cookies():
    """Get AYT_YTDLP_COOKIE value and ensure absolute paths for cookie files"""
    cookie_args = os.environ.get("AYT_YTDLP_COOKIE", "")

    if not cookie_args:
        return cookie_args

    # Split the cookie argument to check for --cookies flag
    parts = cookie_args.split()

    if len(parts) == 2:
        if parts[0] == "--cookies":
            cookie_path = parts[1]
            # Convert to absolute path if it's not already
            if not os.path.isabs(cookie_path):
                cookie_path = os.path.abspath(cookie_path)
                cookie_args = f"{parts[0]} {cookie_path}"

    return cookie_args
