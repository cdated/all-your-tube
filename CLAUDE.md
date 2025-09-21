# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

all-your-tube is a simple Flask web UI for yt-dlp (YouTube downloader). The application provides a web form to submit download requests and stream real-time download progress logs.

## Architecture

### Core Components

- **Main Application** (`src/all_your_tube/app.py`): Single-file Flask application with all routes and logic
- **Templates** (`src/all_your_tube/templates/`): HTML templates for the web interface
  - `index.html`: Main download form
  - `log.html`: Real-time log streaming page
- **Static Files** (`src/all_your_tube/static/`): CSS and other static assets
- **Configuration**: Environment variables control behavior (see Environment Variables section)

### Key Functionality

- **Download Process**: Spawns yt-dlp subprocess with nohup for background execution
- **Log Streaming**: Uses pygtail and Server-Sent Events (SSE) to stream live download logs
- **Directory Management**: Supports organizing downloads into subdirectories
- **Security**: Basic input validation to prevent command injection

## Development Commands

### Running the Application

```bash
# Using the launch script (recommended)
./launch.sh

# Direct poetry execution
poetry run all-your-tube
```

### Code Quality Tools

```bash
# Linting with pylint
poetry run pylint src/all_your_tube/

# Code formatting with black
poetry run black src/

# Import sorting with isort
poetry run isort src/
```

### Dependency Management

```bash
# Install dependencies
poetry install

# Update dependencies
poetry update
```

## Environment Variables

Required:

- `AYT_WORKDIR`: Directory where downloads and logs are stored
- `AYT_YTDLP_COOKIE`: Cookie authentication for yt-dlp
  (e.g., `--cookies /path/to/cookies.txt` or `--cookies-from-browser chrome`)

Optional:

- `AYT_HOST`: Server host (default: "0.0.0.0")
- `AYT_PORT`: Server port (default: 1424)
- `AYT_DEBUG`: Debug mode (default: False)
- `AYT_YTDLP_ARGS`: Custom yt-dlp arguments
  (default: `-f bestvideo+bestaudio -o "%(title)s.%(ext)s" --download-archive archive.txt`)

## URL Structure

The application uses a URL prefix `/yourtube` for all routes. Main routes:

- `/yourtube/`: Main download form
- `/yourtube/save`: POST endpoint for download submission
- `/yourtube/logs/<pid>`: Live log viewing page
- `/yourtube/stream/<pid>`: SSE endpoint for log streaming
- `/yourtube/log_desc/<pid>`: Get download description from logs

## File Structure

```
src/
└── all_your_tube/
    ├── __init__.py      # Package initialization
    ├── app.py           # Main Flask application
    ├── templates/       # Jinja2 templates
    │   ├── index.html   # Download form
    │   └── log.html     # Log streaming page
    └── static/          # Static assets (CSS, etc.)
```

## Dependencies

- Flask: Web framework
- pygtail: Log file tailing for live updates
- werkzeug: WSGI utilities and proxy handling

