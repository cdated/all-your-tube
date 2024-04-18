from __future__ import print_function
from six.moves import input

from datetime import datetime

import io
import json
import hashlib
import os
import subprocess

from shlex import quote

from flask import Flask, Blueprint, render_template, request, redirect, abort, url_for
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
    return dict(url_prefix=PREFIX)


def validate_input(val):
    if val and ";" in val:
        return False
    return True


@bp.route("/save", methods=["POST"])
def download_video():
    path = request.form.get("url")
    target_dir = request.form.get("directory")

    success = True

    if target_dir and "/" in target_dir:
        success = False

    if not validate_input(path):
        success = False

    ytargs = path + ' -o "%(title)s.%(ext)s" &'
    print(ytargs)
    workdir = WORKDIR

    if success and (path and "http" in path):
        if target_dir:
            workdir += target_dir.strip()

        if not os.path.exists(workdir):
            os.mkdir(workdir)

        os.chdir(workdir)

        cmd = "yt-dlp"
        subprocess.run("{} {}".format(quote(cmd), quote(ytargs)), shell=True)
        os.chdir(workdir)

    return render_template("index.html")


@bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")


def main():
    port = int(os.environ.get("PORT", 1424))
    app.debug = os.environ.get("DEBUG", False)

    app.register_blueprint(bp, url_prefix=PREFIX)
    app.run(host="0.0.0.0", port=port, threaded=True)


if __name__ == "__main__":
    main()
