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

## Features

- Web-based interface for yt-dlp downloads
- Real-time log streaming and progress monitoring
- Directory organization for downloads
- Download link generation for completed videos
- Configurable yt-dlp arguments and output formats

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd all-your-tube
```

1. Install dependencies using Poetry:

```bash
poetry install
```

## Configuration

Set up the required environment variables:

### Required

- `AYT_WORKDIR`: Directory where downloads and logs are stored

### Optional

- `AYT_HOST`: Server host (default: "0.0.0.0")
- `AYT_PORT`: Server port (default: 1424)
- `AYT_DEBUG`: Debug mode (default: False)
- `AYT_YTDLP_ARGS`: Custom yt-dlp arguments (default:
  `-f "best[ext=mp4]/best" --restrict-filenames --write-thumbnail
  --embed-thumbnail --convert-thumbnails jpg
   -o "%(uploader)s - %(title).100s.%(ext)s" --paths temp:/tmp --no-part`)
- `AYT_YTDLP_COOKIE`: Cookie authentication for yt-dlp. **Required for most
  platforms** to handle bot detection and access age-restricted content.

Example:

```bash
export AYT_WORKDIR="/path/to/downloads"
export AYT_PORT=8080
export AYT_YTDLP_COOKIE="--cookies-from-browser chrome"
```

### Cookie Authentication

Most video platforms now require authentication to handle bots and control
content access. The `AYT_YTDLP_COOKIE` variable supports two authentication
methods:

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

**Why is this needed?**

- YouTube discontinued username/password authentication in 2024
- Platforms use sophisticated bot detection requiring browser cookies
- Age-restricted and private content requires authenticated sessions
- Cookie-based auth bypasses CAPTCHAs and "Sign in to confirm you're not a bot"
  errors

## Usage

### Running with Docker (Recommended)

**Build and run with Docker:**

```bash
# Build the image
docker build -t all-your-tube .

# Run using the provided script
./run_docker.sh

# Or run manually with proper volume mounts
docker run --rm \
  --user $(id -u):$(id -g) \
  --name all-your-tube \
  -p 1424:1424 \
  -v $(pwd)/downloads:/tmp/downloads \
  -v $(pwd)/cookie:/tmp/cookie \
  -e AYT_YTDLP_COOKIE="--cookies /tmp/cookie" \
  all-your-tube
```

**Using Docker Compose:**

```yaml
# docker-compose.yml
version: '3.8'
services:
  all-your-tube:
    build: .
    ports:
      - "1424:1424"
    volumes:
      - ./downloads:/tmp/downloads
      - ./cookie:/tmp/cookie
    environment:
      - AYT_WORKDIR=/tmp/downloads
      - AYT_YTDLP_COOKIE=--cookies /tmp/cookie
```

### Running Locally

**Development server:**

```bash
# Using the launch script
./launch.sh

# Or using Poetry directly
poetry run all-your-tube-dev
```

**Production server:**

```bash
# Install dependencies including Gunicorn
poetry install

# Run with Gunicorn WSGI server (default command)
poetry run all-your-tube

# Or run Gunicorn directly
poetry run gunicorn --config gunicorn.conf.py all_your_tube.wsgi:application
```

**Environment variables for production:**

```bash
export AYT_WORKERS=4                                    # Number of worker processes (default: 4)
export AYT_HOST=0.0.0.0                                 # Server host (default: 0.0.0.0)
export AYT_PORT=1424                                    # Server port (default: 1424)
export AYT_WORKDIR="/path/to/downloads"                 # Download directory (required)
export AYT_YTDLP_COOKIE="--cookies-from-browser chrome" # Cookie authentication (recommended)
```

### Accessing the Web Interface

1. Open your browser and navigate to `http://localhost:1424/yourtube/`
   (or your configured host/port)
2. Enter a video URL from YouTube, Vimeo, or any supported platform
3. Optionally specify a subdirectory for organization
4. Choose your download method:
   - **Start Download**: Immediate download videos and playlists with
     real-time progress logs.
   - **Create Download Link**: Generates download links for remote
     clients.
5. Monitor progress and download completed files

## Development

### Code Quality Tools

**Linting:**

```bash
poetry run pylint src/all_your_tube/
```

**Code formatting:**

```bash
poetry run black src/
```

**Import sorting:**

```bash
poetry run isort src/
```

### Dependency Management

**Install dependencies:**

```bash
poetry install
```

**Update dependencies:**

```bash
poetry update
```

## Architecture

### Core Components

- **Main Application** (`src/all_your_tube/app.py`): Flask application with
  routes and core logic
- **Queue System** (`src/all_your_tube/queue.py`): Background video
  processing and download management
- **Log Monitoring** (`src/all_your_tube/log_monitoring.py`): Real-time
  file monitoring using watchdog
- **Templates** (`src/all_your_tube/templates/`): HTML templates with pixel art styling
- **Static Files** (`src/all_your_tube/static/`): CSS and JavaScript for the
  web interface

### URL Structure

All routes use the `/yourtube` prefix:

**Main Interface:**

- `/yourtube/`: Main download form
- `/yourtube/save`: POST endpoint for immediate downloads
- `/yourtube/logs/<pid>`: Live log viewing page
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

This application provides a web interface for yt-dlp to download videos.
Please use responsibly.

See [yt-dlp FAQ](https://github.com/yt-dlp/yt-dlp/wiki/FAQ) for their usage guidelines.

**Please Consider:**

- Respect the terms of service of video platforms
- Only download content you have permission to access
- Follow your local laws and regulations
- Use for personal archiving of legally accessible content
- Provide your own authentication (cookies) when required

**This Tool:**

- Provides a web interface for yt-dlp functionality
- Users are responsible for their usage and downloads

**Questions?** Consult the platform's terms of service and your local regulations.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE)
file for details.
