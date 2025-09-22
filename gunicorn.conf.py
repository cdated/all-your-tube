# Gunicorn configuration file
import os

# Server socket
bind = f"{os.environ.get('AYT_HOST', '0.0.0.0')}:{os.environ.get('AYT_PORT', 1424)}"
backlog = 2048

# Worker processes
workers = int(os.environ.get("AYT_WORKERS", 4))
worker_class = "sync"
worker_connections = 1000
timeout = 300
keepalive = 2

# Restart workers after this many requests, with up to jitter requests variation
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "all-your-tube"

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment and configure if using HTTPS)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
