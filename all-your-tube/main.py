"""
Collect yt-dlp parameters through a web form using Flask.
"""

import logging
import os
import subprocess
from datetime import datetime
from shlex import quote

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


@bp.route("/logs/<pid>")
def render_live_logs(pid):
    """Render log page"""
    return render_template("log.html", pid=pid)


@bp.route("/log_desc/<pid>")
def log_desc(pid):
    """Get the first 'download' line from the logs to describe the job."""
    logfile = WORKDIR + "/" + pid + ".log"

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
    logfile = WORKDIR + "/" + pid + ".log"

    def generate():
        for line in Pygtail(logfile, every_n=1):
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

    if target_dir and "/" in target_dir:
        success = False

    if not validate_input(path):
        success = False

    ytargs = quote(path) + ' -o "%(title)s.%(ext)s"'
    workdir = WORKDIR
    pid = None

    if success and (path and "http" in path):
        if target_dir:
            workdir += target_dir.strip()

        if not os.path.exists(workdir):
            os.mkdir(workdir)

        os.chdir(workdir)

        # Use a timestamp to refer to the download logs
        # Redirct to the logs page to watch progress
        cmd = quote("yt-dlp")
        pid = str(int(datetime.now().timestamp()))
        job_log = pid + ".log"
        command = f"nohup {cmd} {ytargs} >> {job_log} && echo 'Download Complete' >> {job_log}"
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

    if pid:
        app.logger.info("Redirecting to logs pag for %s", pid)
        return redirect(url_for("bp.render_live_logs", pid=pid))

    return render_template("index.html")


@bp.route("/", methods=["GET"])
def index():
    """Create download request form"""
    return render_template("index.html")


def main():
    """Run Flask server to request yt-dlp commands"""
    port = int(os.environ.get("PORT", 1424))
    app.debug = os.environ.get("DEBUG", False)

    app.register_blueprint(bp, url_prefix=PREFIX)
    app.run(host="0.0.0.0", port=port, threaded=True)


if __name__ == "__main__":
    main()
