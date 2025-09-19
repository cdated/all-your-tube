"""
Log monitoring functionality for all-your-tube.

Handles real-time log file monitoring using filesystem events.
"""

import logging
from pathlib import Path
from queue import Empty, Queue

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Global dictionary to manage active log streams
active_streams = {}
log_observers = {}

# Get logger for this module
logger = logging.getLogger(__name__)


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
                f.seek(0, 2)
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
            logger.error("Error reading log file %s: %s", self.log_file_path, e)


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
    logger.info("Started monitoring log file: %s", log_file)

    return observer, handler


def cleanup_stream(stream_id):
    """Clean up resources for a specific stream"""
    if stream_id in active_streams:
        del active_streams[stream_id]
    if stream_id in log_observers:
        log_observers[stream_id].stop()
        log_observers[stream_id].join()
        del log_observers[stream_id]


def generate_log_stream(stream_id, log_file, app_logger):
    """Generate log stream data for Server-Sent Events"""

    # Check if log file exists
    if not log_file.exists():
        yield "data: Log file not found.\n\n"
        yield "data: The download may not have started or the file was moved.\n\n"
        yield "data: Expected location: " + str(log_file) + "\n\n"
        yield "data: \n\n"
        yield "data: ---^-^---\n\n"
        return

    is_completed = False
    with open(log_file, "r", encoding="utf-8") as f:
        app_logger.debug("checking completed")
        content = f.read()
        is_completed = "Download Complete" in content
        logger.debug("found completed")
        for line in content.split("\n"):
            line = line.rstrip("\n\r")
            if line and "nohup:" not in line:
                yield f"data: {line}\n\n"

    app_logger.debug(f"is completed {is_completed}")
    if is_completed:
        return

    # For active downloads, use file monitoring
    log_queue = Queue()
    active_streams[stream_id] = log_queue
    try:
        # Start monitoring the log file
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
                    # During download, send heartbeat to keep connection alive
                    yield "data: \n\n"
                    continue

    finally:
        # Cleanup resources
        cleanup_stream(stream_id)
