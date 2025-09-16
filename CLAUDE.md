# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

all-your-tube is a simple Flask web UI for yt-dlp (YouTube downloader). The application provides a web form to submit download requests and stream real-time download progress logs.

## Architecture

### Core Components

- **Main Application** (`all-your-tube/main.py`): Single-file Flask application with all routes and logic
- **Templates** (`all-your-tube/templates/`): HTML templates for the web interface
  - `index.html`: Main download form
  - `log.html`: Real-time log streaming page
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
poetry run python all-your-tube/main.py
```

### Code Quality Tools
```bash
# Linting with pylint
poetry run pylint all-your-tube/main.py

# Code formatting with black
poetry run black all-your-tube/main.py

# Import sorting with isort
poetry run isort all-your-tube/main.py
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

Optional:
- `AYT_HOST`: Server host (default: "0.0.0.0")
- `AYT_PORT`: Server port (default: 1424)
- `AYT_DEBUG`: Debug mode (default: False)
- `AYT_YTDLP_ARGS`: Custom yt-dlp arguments (default: `-f bestvideo+bestaudio -o "%(title)s.%(ext)s" --download-archive archive.txt`)

## URL Structure

The application uses a URL prefix `/yourtube` for all routes. Main routes:
- `/yourtube/`: Main download form
- `/yourtube/save`: POST endpoint for download submission
- `/yourtube/logs/<pid>`: Live log viewing page
- `/yourtube/stream/<pid>`: SSE endpoint for log streaming
- `/yourtube/log_desc/<pid>`: Get download description from logs

## File Structure

```
all-your-tube/
├── main.py              # Main Flask application
└── templates/
    ├── index.html       # Download form
    └── log.html         # Log streaming page
```

## Dependencies

- Flask: Web framework
- pygtail: Log file tailing for live updates
- werkzeug: WSGI utilities and proxy handling