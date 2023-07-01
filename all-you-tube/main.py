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

PREFIX="/yourtube"

bp = Blueprint('bp', __name__, static_folder='static', template_folder='templates')
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)


@app.context_processor
def inject_dict_for_all_templates():
    return dict(url_prefix=PREFIX)


def validate_input(val):
    if val and ';' in val:
        return False
    return True

@bp.route('/save', methods=['POST'])
def download_video():
    path = request.form.get("url")
    directory = request.form.get("directory")
    password = request.form.get("password")
    token = request.form.get("token")

    print(path)
    print(directory)
    print(password)
    print(token)

    success = True
    if token != 'zombiemao':
        success = False

    if directory and '/' in directory:
        success = False

    if not validate_input(path) or not validate_input(password):
        success = False

    ytargs = path
    if password:
        ytargs = "{} --video-password {}".format(path, password)
    print(ytargs)

    if success and (path and 'http' in path):
        #workdir = "/mnt/raft/plex/YouTube_Unsorted"
        workdir = "/mnt/raft/matthew"
#        if directory:
#            workdir = "/mnt/vault/Brandon/YouTube/" + directory.strip()

        if not os.path.exists(workdir):
            os.mkdir(workdir)

        os.chdir(workdir)

        if "twitter" in ytargs:
            cmd = "youtube-dl"
        else:
            cmd = "/home/cdated/yt-save.sh"
        subprocess.run('{} {}'.format(quote(cmd), quote(ytargs)), shell=True)
        os.chdir(workdir)

    return render_template('index.html')


@bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')


def main():
    port = int(os.environ.get('PORT', 1424))
    app.debug = os.environ.get('DEBUG', False)

    app.register_blueprint(bp, url_prefix=PREFIX)
    print(app.url_map)
    app.run(host='10.0.1.4', port=port)


if __name__ == '__main__':
    main()
