"""
Collect yt-dlp parameters through a web form using Flask.
"""

from __future__ import print_function

import os
import subprocess
import time

from pygtail import Pygtail
from datetime import datetime
from shlex import quote

from flask import Response, stream_with_context
from flask import redirect, url_for, send_from_directory
from flask import Flask, Blueprint, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

PREFIX = "/yourtube"
WORKDIR = os.environ.get("AYT_WORKDIR")
if not WORKDIR:
    raise RuntimeError("AYT_WORKDIR env variable must be set")

bp = Blueprint("bp", __name__, static_folder="static", template_folder="templates")
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)


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
def send_report(pid):
    # logfile = pid + ".log"
    # return send_from_directory(WORKDIR, logfile)
    return render_template("log.html", pid=pid)


@bp.route("/log_desc/<pid>")
def log_desc(pid):
    """Get the first 'download' line from the logs to describe the job."""
    logfile = WORKDIR + "/" + pid + ".log"

    with open(logfile, "r") as f:
        while True:
            line = f.readline()
            if "download" in line:
                break
        desc = str.encode(line)

    return app.response_class(desc, mimetype="text/plain")


@bp.route("/stream/<pid>")
def stream(pid):
    logfile = WORKDIR + "/" + pid + ".log"

    # def generate():
    #     yield "Log data..."
    #     with open(logfile, "r") as f:
    #         while True:
    #             yield f.read(1024)

    def generate():
        for line in Pygtail(logfile, every_n=1):
            yield "data:" + str(line) + "\n\n"

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

    ytargs = path + ' -o "%(title)s.%(ext)s"'
    print(ytargs)
    workdir = WORKDIR
    pid = None

    if success and (path and "http" in path):
        if target_dir:
            workdir += target_dir.strip()

        if not os.path.exists(workdir):
            os.mkdir(workdir)

        os.chdir(workdir)

        # Fire and forget for now
        cmd = quote("yt-dlp")
        pid = str(int(datetime.now().timestamp()))
        job_log = pid + ".log"
        command = f"nohup {cmd} {ytargs} && echo 'Download Complete' > {job_log}"
        subprocess.Popen(
            command,
            shell=True,
            stderr=open(job_log, "a"),
            stdout=open(job_log, "a"),
            preexec_fn=os.setpgrp,
        ).pid
        os.chdir(workdir)

    if pid:
        return redirect(url_for("bp.send_report", pid=pid))
    else:
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
