"""
Collect yt-dlp parameters through a web form using Flask.
"""

import logging
import os
import subprocess
from datetime import datetime
from shlex import quote
from pathlib import Path
import urllib.parse

from flask import (
    Blueprint,
    Flask,
    Response,
    redirect,
    render_template,
    request,
    url_for,
)
from pygtail import Pygtail
from werkzeug.middleware.proxy_fix import ProxyFix

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
handler = logging.FileHandler("app.log")  # Log to a file
app.logger.addHandler(handler)


@app.context_processor
def inject_dict_for_all_templates():
    """Inject URL location"""
    return {"url_prefix": PREFIX}


def validate_input(val):
    """Barest minimum code injection check"""
    if val and ";" in val:
        return False
    return True


def logfile_path(pid, subdir):
    """Return the logfile for a given PID and subdir"""
    subdir = urllib.parse.unquote(subdir)
    if subdir == "default":
        logfile = WORKDIR / Path(pid + ".log")
    else:
        logfile = WORKDIR / Path(subdir) / Path(pid + ".log")
    if not logfile.is_file():
        raise RuntimeError(f"Log file {logfile} does not exist")
    return logfile


@bp.route("/logs/<pid>")
def render_live_logs(pid):
    """Render log page"""
    subdir = request.args.get("subdir", "default")
    return render_template("log.html", pid=pid, subdir=subdir)


@bp.route("/log_desc/<pid>")
def log_desc(pid):
    """Get the first 'download' line from the logs to describe the job."""
    subdir = request.args.get("subdir")
    logfile = logfile_path(pid, subdir)

    with open(logfile, "r", encoding="utf-8") as f:
        while True:
            line = f.readline()
            if "[download]" in line:
                break
        desc = str.encode(line)

    return app.response_class(desc, mimetype="text/plain")


@bp.route("/stream/<pid>")
def stream(pid):
    """Stream the download log data"""
    subdir = request.args.get("subdir")
    logfile = logfile_path(pid, subdir)

    def generate():
        for line in Pygtail(str(logfile), every_n=1):
            data = "data:" + str(line) + "\n\n"
            if "nohup:" not in data:
                yield data

    return Response(generate(), mimetype="text/event-stream")


@bp.route("/save", methods=["POST"])
def download_video():
    """Perform yt-dlp command from form data"""
    path = request.form.get("url")
    target_dir = request.form.get("directory")

    success = True

    if target_dir and ".." in target_dir:
        success = False

    if not validate_input(path):
        success = False

    default_params = (
        '-f bestvideo+bestaudio -o "%(title)s.%(ext)s" --download-archive archive.txt'
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
        # Redirct to the logs page to watch progress
        cmd = quote("yt-dlp")
        pid = str(int(datetime.now().timestamp()))
        job_log = pid + ".log"
        command = f"nohup {cmd} {ytargs} &>> {job_log} && echo 'Download Complete' &>> {job_log}"
        app.logger.info("Running command: %s", command)

        with open(job_log, "w", encoding="utf-8") as f:
            f.write("Starting...")

        # pylint: disable=consider-using-with
        # pylint: disable=subprocess-popen-preexec-fn
        subprocess.Popen(
            command,
            shell=True,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            preexec_fn=os.setpgrp,
        )
        os.chdir(workdir)

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
