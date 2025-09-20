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
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.middleware.proxy_fix import ProxyFix

from . import log_monitoring

PREFIX = "/yourtube"
WORKDIR = os.environ.get("AYT_WORKDIR")

if not WORKDIR:
    raise RuntimeError("AYT_WORKDIR env variable must be set")
WORKDIR = Path(WORKDIR)
if not WORKDIR.is_dir():
    raise RuntimeError(f"AYT_WORKDIR {WORKDIR} does not exist")

bp = Blueprint("bp", __name__, static_folder="static", template_folder="templates")
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)


# Configure Flask logging
app.logger.setLevel(logging.INFO)  # Set log level to INFO
log_handler = logging.FileHandler("app.log")  # Log to a file
app.logger.addHandler(log_handler)


@app.context_processor
def inject_dict_for_all_templates():
    """Inject URL location"""
    return {"url_prefix": PREFIX}


def validate_input(val):
    """Barest minimum code injection check"""
    if val and ";" in val:
        return False
    return True


def log_filepath(pid, subdir):
    """Return the logfile for a given PID and subdir"""
    subdir = urllib.parse.unquote(subdir)
    if subdir == "default":
        logfile = WORKDIR / Path(pid + ".log")
    else:
        logfile = WORKDIR / Path(subdir) / Path(pid + ".log")
    return logfile


@bp.route("/logs/<pid>")
def render_live_logs(pid):
    """Render log page"""
    subdir = request.args.get("subdir", "default")
    return render_template("log.html", pid=pid, subdir=subdir)


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
        '-f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best" '
        '-o "%(title)s.%(ext)s" --download-archive archive.txt --merge-output-format mp4 '
        "--no-mtime --no-playlist --extract-flat false --write-info-json "
        "--embed-metadata --add-metadata"
    )
    yt_env_args = os.environ.get("AYT_YTDLP_ARGS", default_params)
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
        cmd = quote("yt-dlp")
        pid = str(int(datetime.now().timestamp()))
        job_log = pid + ".log"
        command = f"nohup {cmd} {ytargs} &>> {job_log} && echo 'Download Complete' &>> {job_log}"
        app.logger.info("Running command: %s", command)

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

    # Fallback for non-AJAX requests (original behavior)
    subdir = urllib.parse.quote_plus(target_dir)
    if pid:
        app.logger.info("Redirecting to logs page for %s", pid)
        return redirect(url_for("bp.render_live_logs", pid=pid, subdir=subdir))

    return render_template("index.html")


@bp.route("/", methods=["GET"])
def index():
    """Create download request form"""
    return render_template("index.html")


def main():
    """Run Flask server to request yt-dlp commands"""

    host = os.environ.get("AYT_HOST", "0.0.0.0")
    port = int(os.environ.get("AYT_PORT", 1424))
    app.debug = os.environ.get("AYT_DEBUG", False)

    app.register_blueprint(bp, url_prefix=PREFIX)
    app.run(host=host, port=port, threaded=True)


if __name__ == "__main__":
    main()
