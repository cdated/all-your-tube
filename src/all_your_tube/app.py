"""
Collect yt-dlp parameters through a web form using Flask.
"""

import logging
import os
import subprocess
import urllib.parse
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue
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
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
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

# Global dictionary to manage active log streams
active_streams = {}
log_observers = {}

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
    if not logfile.is_file():
        raise RuntimeError(f"Log file {logfile} does not exist")
    return logfile


@bp.route("/logs/<pid>")
def render_live_logs(pid):
    """Render log page"""
    subdir = request.args.get("subdir", "default")
    return render_template("log.html", pid=pid, subdir=subdir)


class LogFileHandler(FileSystemEventHandler):
    """Handle filesystem events for log files"""

    def __init__(self, log_queue, log_file_path):
        super().__init__()
        self.log_queue = log_queue
        self.log_file_path = Path(log_file_path)
        self.file_position = 0
        self._read_existing_content()

    def _read_existing_content(self):
        """Get end of file offset"""
        if self.log_file_path.exists():
            with open(self.log_file_path, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()
                for line in existing_lines:
                    if "nohup:" in line:
                        continue
                    self.log_queue.put(line)
                self.file_position = f.tell()

    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return

        if Path(event.src_path) == self.log_file_path:
            self._read_new_lines()

    def _read_new_lines(self):
        """Read only new lines from the log file"""
        try:
            if not self.log_file_path.exists():
                return

            with open(self.log_file_path, "r", encoding="utf-8") as f:
                f.seek(self.file_position)
                new_lines = f.readlines()
                self.file_position = f.tell()

                for line in new_lines:
                    line = line.rstrip("\n\r")
                    if line and "nohup:" not in line:
                        self.log_queue.put(line)

        except (IOError, OSError) as e:
            app.logger.error("Error reading log file %s: %s", self.log_file_path, e)


def start_log_monitoring(stream_id, log_queue, log_file):
    """Start monitoring a log file for changes"""
    # Stop existing observers if any
    if stream_id in log_observers:
        log_observers[stream_id].stop()
        log_observers[stream_id].join()  # Wait until it actually stops

    # Create new observer
    observer = Observer()
    handler = LogFileHandler(log_queue, log_file)

    # Watch the directory containing the log file
    watch_dir = log_file.parent
    observer.schedule(handler, str(watch_dir), recursive=False)
    observer.start()

    log_observers[stream_id] = observer
    app.logger.info("Started monitoring log file: %s", log_file)

    return observer, handler


@bp.route("/stream/<pid>")
def stream(pid):
    """Stream the download log data using file watching"""
    subdir = request.args.get("subdir")
    stream_id = f"{pid}_{subdir or 'default'}"

    def generate():
        log_queue = Queue()

        # Store the queue for this stream
        active_streams[stream_id] = log_queue

        # Start monitoring the log file
        log_file = log_filepath(pid, subdir)
        observer, _ = start_log_monitoring(stream_id, log_queue, log_file)

        if not observer:
            yield "data: Error: Could not start log monitoring\n\n"
            return

        # Read any existing content first
        if log_file.exists():
            while True:
                try:
                    line = log_queue.get(timeout=30)
                    yield f"data: {line}\n\n"

                    # Check for completion
                    if "Download Complete" in line:
                        break
                except Empty:
                    # Send heartbeat to keep connection alive
                    yield "data: \n\n"
                    continue

        # Cleanup
        if stream_id in active_streams:
            del active_streams[stream_id]
        if stream_id in log_observers:
            log_observers[stream_id].stop()
            log_observers[stream_id].join()
            del log_observers[stream_id]

    response = Response(generate(), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"

    return response


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
