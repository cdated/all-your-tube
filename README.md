# All Your Tube

A minimalist web interface for yt-dlp that makes video downloading simple and
accessible. Download videos to your server or locally from sites like YouTube
and Vimeo.

![Demo](docs/all-your-tube-demo.gif)

## What Makes It Special

- **Download Link Generation**: Create links for client-side downloads
- **Real-Time Progress**: Watch downloads happen live with streaming logs
- **Organized Downloads**: Organize videos into custom folders
- **Zero Client Software**: Just a web browser - works on any device

## Perfect For

- **Media Archivists**: Batch download and organize video collections
- **Content Creators**: Download reference material and inspiration
- **Educators**: Save educational content for offline viewing
- **Self-Hosters**: Run your own private video download service

## Quick Start

### Docker

```bash
# Build and run
docker build -t all-your-tube .
./run_docker.sh
```

Or manually:

```bash
docker run --rm \
  --user $(id -u):$(id -g) \
  -p 1425:1424 \
  -v $(pwd)/downloads:/tmp/downloads \
  -v $(pwd)/cookie:/tmp/cookie \
  -e AYT_YTDLP_COOKIE="--cookies /tmp/cookie" \
  all-your-tube
```

### Local Development

```bash
# Install dependencies
poetry install

# Set required environment
export AYT_WORKDIR="/path/to/downloads"
export AYT_YTDLP_COOKIE="--cookies-from-browser chrome"

# Run development server
poetry run all-your-tube
```

### Production

```bash
# Set environment variables
export AYT_WORKDIR="/path/to/downloads"
export AYT_YTDLP_COOKIE="--cookies-from-browser chrome"
export AYT_WORKERS=4

# Run with Gunicorn
poetry run all-your-tube
```

## Configuration

### Required Environment Variables

- **`AYT_WORKDIR`**: Directory where downloads and logs are stored
- **`AYT_YTDLP_COOKIE`**: Cookie authentication for yt-dlp (**Required for most
  platforms**)

### Optional Environment Variables

- `AYT_HOST`: Server host (default: "0.0.0.0")
- `AYT_PORT`: Server port (default: 1424)
- `AYT_DEBUG`: Debug mode (default: False)
- `AYT_WORKERS`: Number of worker processes for production (default: 4)
- `AYT_YTDLP_ARGS`: Custom yt-dlp arguments (default:
  `-f "best[ext=mp4]/best" --restrict-filenames --write-thumbnail --embed-thumbnail --convert-thumbnails jpg -o "%(uploader)s - %(title).100s.%(ext)s" --paths temp:/tmp --no-part`)

### Cookie Authentication

Most video platforms require authentication to handle bots and access content.
Set up cookies using:

**Browser Cookie Extraction (Recommended):**

```bash
# Chrome/Chromium
export AYT_YTDLP_COOKIE="--cookies-from-browser chrome"

# Firefox
export AYT_YTDLP_COOKIE="--cookies-from-browser firefox"
```

**Manual Cookie File:**

```bash
export AYT_YTDLP_COOKIE="--cookies /path/to/cookies.txt"
```

**Why cookies are needed:**

- YouTube discontinued username/password authentication in 2024
- Platforms use sophisticated bot detection requiring browser cookies
- Age-restricted and private content requires authenticated sessions

## Using the Web Interface

1. Open `http://localhost:1424/yourtube/` in your browser
1. Enter a video URL from YouTube, Vimeo, or any supported platform
1. Optionally specify a subdirectory for organization
1. Choose your download method:
   - **Start Download**: Immediate download with real-time progress logs
   - **Create Download Link**: Generate download links for remote clients
1. Monitor progress and download completed files

## Development

**Code Quality Tools:**

```bash
# Format all code and documentation
poetry run fmt

# Individual tools
poetry run pylint src/all_your_tube/
poetry run black src/
poetry run isort src/
poetry run mdformat README.md
```

**Dependency Management:**

```bash
poetry install    # Install dependencies
poetry update     # Update dependencies
```

## Architecture

### Core Components

- **Main Application** (`src/all_your_tube/app.py`): Flask application with
  routes and core logic
- **Queue System** (`src/all_your_tube/queue.py`): Background video processing
  and download management
- **Log Monitoring** (`src/all_your_tube/log_monitoring.py`): Real-time file
  monitoring using watchdog
- **Templates** (`src/all_your_tube/templates/`): HTML templates with pixel art
  styling
- **Static Files** (`src/all_your_tube/static/`): CSS and JavaScript for the web
  interface

### URL Structure

All routes use the `/yourtube` prefix:

**Main Interface:**

- `/yourtube/`: Main download form
- `/yourtube/save`: POST endpoint for immediate downloads
- `/yourtube/stream/<pid>`: SSE endpoint for log streaming

**Queue System:**

- `/yourtube/queue-download`: POST endpoint to queue high-quality downloads
- `/yourtube/queue-status/<id>`: Get status of queued download
- `/yourtube/queue-list`: List all queue items
- `/yourtube/queue-download-file/<id>`: Download completed video file

## Dependencies

- Flask: Web framework
- watchdog: Filesystem event monitoring for real-time log updates
- werkzeug: WSGI utilities and proxy handling
- yt-dlp: YouTube downloader (external dependency)

## Usage Guidelines

This application provides a web interface for yt-dlp to download videos. Please
use responsibly.

See [yt-dlp FAQ](https://github.com/yt-dlp/yt-dlp/wiki/FAQ) for their usage
guidelines.

**Please Consider:**

- Respect the terms of service of video platforms
- Only download content you have permission to access
- Follow your local laws and regulations
- Use for personal archiving of legally accessible content
- Provide your own authentication (cookies) when required

**This Tool:**

- Provides a web interface for yt-dlp functionality
- Users are responsible for their usage and downloads

**Questions?** Consult the platform's terms of service and your local
regulations.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file
for details.
