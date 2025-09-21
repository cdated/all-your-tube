"""
Collect yt-dlp parameters through a web form using Flask.
"""

import logging
import os
import subprocess
import urllib.parse
from datetime import datetime
from pathlib import Path
from shlex import quote

from flask import (
    Blueprint,
    Flask,
    Response,
    jsonify,
    render_template,
    request,
    url_for,
)
from werkzeug.middleware.proxy_fix import ProxyFix

from . import log_monitoring
from .queue import queue_bp
from .utils import get_cookies, validate_input

PREFIX = "/yourtube"
WORKDIR = os.environ.get("AYT_WORKDIR")

if not WORKDIR:
    raise RuntimeError("AYT_WORKDIR env variable must be set")
WORKDIR = Path(WORKDIR)
if not WORKDIR.is_dir():
    WORKDIR.mkdir(parents=True, exist_ok=True)


bp = Blueprint("bp", __name__, static_folder="static", template_folder="templates")
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)


# Configure Flask logging
app.logger.setLevel(logging.INFO)  # Set log level to INFO
log_dir = Path(os.environ.get("AYT_WORKDIR", ".")) / "logs"
log_dir.mkdir(exist_ok=True)

# Ensure cache directory exists in WORKDIR
cache_dir = Path(os.environ.get("AYT_WORKDIR", ".")) / ".cache"
cache_dir.mkdir(exist_ok=True)
os.environ["XDG_CACHE_HOME"] = str(cache_dir)

log_handler = logging.FileHandler(log_dir / "app.log")  # Log to logs directory
app.logger.addHandler(log_handler)


@app.context_processor
def inject_dict_for_all_templates():
    """Inject URL location"""
    return {"url_prefix": PREFIX}


def log_filepath(pid, subdir):
    """Return the logfile for a given PID and subdir"""
    subdir = urllib.parse.unquote(subdir)
    if subdir == "default":
        logfile = WORKDIR / Path(pid + ".log")
    else:
        logfile = WORKDIR / Path(subdir) / Path(pid + ".log")
    return logfile


@bp.route("/stream/<pid>")
def stream(pid):
    """Stream the download log data using file watching"""
    subdir = request.args.get("subdir")
    stream_id = f"{pid}_{subdir or 'default'}"
    log_file = log_filepath(pid, subdir)

    response = Response(
        log_monitoring.generate_log_stream(stream_id, log_file, app.logger),
        mimetype="text/event-stream",
    )
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"

    return response


@bp.route("/save", methods=["POST"])
def download_video():
    """Perform yt-dlp command from form data"""
    path = request.form.get("url")
    target_dir = request.form.get("directory")

    success = True
    error_message = None

    if target_dir and ".." in target_dir:
        success = False
        error_message = "Invalid directory path"

    if not validate_input(path):
        success = False
        error_message = "Invalid URL format"

    default_params = (
        '-f "best[ext=mp4]/best" --restrict-filenames --write-thumbnail '
        "--embed-thumbnail --convert-thumbnails jpg "
        '-o "%(uploader)s - %(title).100s.%(ext)s" '
        "--paths temp:/tmp --no-part "
    )
    yt_env_args = os.environ.get("AYT_YTDLP_ARGS", default_params)

    # Add cookie support if AYT_YTDLP_COOKIE is set
    cookie_args = get_cookies()
    if cookie_args:
        yt_env_args += f" {cookie_args}"

    ytargs = yt_env_args + " " + quote(path)
    workdir = WORKDIR
    pid = None

    if success and (path and "http" in path):
        if target_dir:
            workdir = workdir / Path(target_dir)
        else:
            target_dir = "default"

        if not workdir.is_dir():
            workdir.mkdir(mode=0o774, parents=True, exist_ok=True)

        os.chdir(workdir)

        # Use a timestamp to refer to the download logs
        pid = str(int(datetime.now().timestamp()))
        job_log = pid + ".log"
        app.logger.info("Running with yt-dlp args: %s", ytargs)

        with open(job_log, "w", encoding="utf-8") as f:
            f.write("Starting...\n")

        # pylint: disable=consider-using-with
        subprocess.Popen(
            [
                "/bin/bash",
                "-c",
                f"yt-dlp {ytargs} >> {job_log} 2>&1 && echo 'Download Complete' >> {job_log}",
            ],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            start_new_session=True,
        )

    # Check if this is an AJAX request
    if (
        request.headers.get("Content-Type") == "application/json"
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    ):
        if success and pid:
            subdir = urllib.parse.quote_plus(target_dir)
            return jsonify(
                {
                    "success": True,
                    "pid": pid,
                    "subdir": subdir,
                    "stream_url": url_for("bp.stream", pid=pid, subdir=subdir),
                }
            )

        return jsonify(
            {
                "success": False,
                "error": error_message or "Invalid URL or missing required fields",
            }
        )

    return render_template("index.html")


@bp.route("/", methods=["GET"])
def index():
    """Create download request form"""
    return render_template("index.html")


# Register blueprints at module level for both dev and production
app.register_blueprint(bp, url_prefix=PREFIX)
app.register_blueprint(queue_bp, url_prefix=PREFIX)


def main():
    """Run Flask development server"""
    host = os.environ.get("AYT_HOST", "0.0.0.0")
    port = int(os.environ.get("AYT_PORT", 1424))
    app.debug = os.environ.get("AYT_DEBUG", False)

    app.run(host=host, port=port, threaded=True)


if __name__ == "__main__":
    main()
