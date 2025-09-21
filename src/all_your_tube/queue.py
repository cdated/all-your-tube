"""
Queue system for high-quality video downloads with background processing.
"""

import json
import logging
import os
import subprocess
import threading
from datetime import datetime
from pathlib import Path

from flask import Blueprint, Response, jsonify, request

# Get WORKDIR from environment
WORKDIR = os.environ.get("AYT_WORKDIR")
if not WORKDIR:
    raise RuntimeError("AYT_WORKDIR env variable must be set")
WORKDIR = Path(WORKDIR)

# Queue system globals
QUEUE_DIR = WORKDIR / "queue"
QUEUE_DIR.mkdir(exist_ok=True)

# In-memory queue storage (for simplicity - could be replaced with Redis/DB)
download_queue = {}
queue_lock = threading.Lock()

# Create blueprint for queue routes
queue_bp = Blueprint("queue", __name__)


def _validate_input(val):
    """Barest minimum code injection check"""
    if val and ";" in val:
        return False
    return True


@queue_bp.route("/queue-download", methods=["POST"])
def queue_download():
    """Queue a high-quality video for background processing"""
    url = request.form.get("url")
    quality = request.form.get("quality", "best")  # best, 1080p, 720p, etc.

    if not url or not _validate_input(url):
        return jsonify({"error": "Invalid URL"}), 400

    # Generate unique queue ID
    queue_id = str(int(datetime.now().timestamp()))

    # Get video metadata for title
    cookie_args = os.environ.get("AYT_YTDLP_COOKIE", "")
    cmd = ["yt-dlp", "--dump-json", "--no-download"]
    if cookie_args:
        cmd.extend(cookie_args.split())
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)

    if result.returncode != 0:
        return jsonify({"error": "Failed to get video metadata"}), 400

    metadata = json.loads(result.stdout)
    title = metadata.get("title", "Unknown Video")

    # Add to queue
    with queue_lock:
        download_queue[queue_id] = {
            "id": queue_id,
            "url": url,
            "title": title,
            "quality": quality,
            "status": "queued",
            "progress": 0,
            "created_at": datetime.now().isoformat(),
            "file_path": None,
            "error": None,
        }

    # Start processing in background
    threading.Thread(target=process_queue_item, args=(queue_id,), daemon=True).start()

    logging.info("Queued download %s: %s", queue_id, title)
    return jsonify(
        {"success": True, "queue_id": queue_id, "title": title, "status": "queued"}
    )


@queue_bp.route("/queue-status/<queue_id>")
def queue_status(queue_id):
    """Get status of a queued download"""
    with queue_lock:
        if queue_id not in download_queue:
            return jsonify({"error": "Queue item not found"}), 404

        item = download_queue[queue_id].copy()

    return jsonify(item)


@queue_bp.route("/queue-list")
def queue_list():
    """Get list of all queue items"""
    with queue_lock:
        items = list(download_queue.values())

    # Sort by creation time, newest first
    items.sort(key=lambda x: x["created_at"], reverse=True)
    return jsonify({"items": items})


@queue_bp.route("/queue-download-file/<queue_id>")
def queue_download_file(queue_id):
    """Download the processed file"""
    with queue_lock:
        if queue_id not in download_queue:
            return jsonify({"error": "Queue item not found"}), 404

        item = download_queue[queue_id]

        if item["status"] != "completed":
            return jsonify({"error": "Download not ready"}), 400

        file_path = item["file_path"]

    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    def generate():
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                yield chunk

    filename = os.path.basename(file_path)
    return Response(
        generate(),
        headers={
            "Content-Type": "video/mp4",
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


def _build_format_selector(quality):
    """Build yt-dlp format selector based on quality setting."""
    if quality == "best":
        return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
    height_limit = quality.replace('p', '')
    return (
        f"bestvideo[height<={height_limit}][ext=mp4]+"
        f"bestaudio[ext=m4a]/best[ext=mp4]"
    )


def _build_ytdlp_command(url, quality, output_template):
    """Build yt-dlp command arguments."""
    format_selector = _build_format_selector(quality)
    cookie_args = os.environ.get("AYT_YTDLP_COOKIE", "")

    cmd = ["yt-dlp"]
    if cookie_args:
        cmd.extend(cookie_args.split())

    cmd.extend([
        "-f",
        format_selector,
        "--merge-output-format",
        "mp4",
        "-o",
        output_template,
        "--no-playlist",
        url,
    ])

    return cmd


def _monitor_download_progress(process, queue_id):
    """Monitor download progress and update queue status."""
    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break

        if output and "[download]" in output and "%" in output:
            try:
                # Extract progress percentage
                progress_str = output.split("%")[0].split()[-1]
                progress = float(progress_str)
                with queue_lock:
                    download_queue[queue_id]["progress"] = progress
            except (ValueError, IndexError):
                pass


def _handle_download_completion(queue_id, return_code, output_dir):
    """Handle download completion and update queue status."""
    if return_code == 0:
        # Find the downloaded file
        video_files = list(output_dir.glob("*.mp4"))
        if video_files:
            with queue_lock:
                download_queue[queue_id]["status"] = "completed"
                download_queue[queue_id]["progress"] = 100
                download_queue[queue_id]["file_path"] = str(video_files[0])
            logging.info("Queue item %s completed successfully", queue_id)
        else:
            with queue_lock:
                download_queue[queue_id]["status"] = "failed"
                download_queue[queue_id]["error"] = "No video file found"
    else:
        with queue_lock:
            download_queue[queue_id]["status"] = "failed"
            download_queue[queue_id]["error"] = "Download failed"


def process_queue_item(queue_id):
    """Background worker to process a queue item"""
    with queue_lock:
        if queue_id not in download_queue:
            return
        item = download_queue[queue_id]
        item["status"] = "processing"

    try:
        url = item["url"]
        quality = item["quality"]

        # Create output directory
        output_dir = QUEUE_DIR / queue_id
        output_dir.mkdir(exist_ok=True)

        # Clean title for filename
        safe_title = "".join(
            c for c in item["title"] if c.isalnum() or c in (" ", "-", "_")
        ).strip()[:50]
        output_template = str(output_dir / f"{safe_title}.%(ext)s")

        cmd = _build_ytdlp_command(url, quality, output_template)
        logging.info("Processing queue item %s: %s", queue_id, " ".join(cmd))

        # Run download and monitor progress
        with subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=output_dir,
        ) as process:
            _monitor_download_progress(process, queue_id)
            return_code = process.poll()

        _handle_download_completion(queue_id, return_code, output_dir)

    except (subprocess.SubprocessError, OSError, json.JSONDecodeError) as e:
        logging.error("Queue processing error for %s: %s", queue_id, str(e))
        with queue_lock:
            download_queue[queue_id]["status"] = "failed"
            download_queue[queue_id]["error"] = str(e)
