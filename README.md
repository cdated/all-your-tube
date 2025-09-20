# All Your Tube

A minimalist web interface for yt-dlp that makes video downloading simple and
accessible. Download videos to your server or locally from YouTube, Vimeo,
etc. through an intuitive web UI.

![Demo](docs/all-your-tube-demo.gif)

## What Makes It Special

- **Download Links**: Create links for client-side downloads.
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

2. Install dependencies using Poetry:

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
  `-f bestvideo+bestaudio -o "%(title)s.%(ext)s" --download-archive archive.txt`)

Example:

```bash
export AYT_WORKDIR="/path/to/downloads"
export AYT_PORT=8080
```

## Usage

### Running with Docker (Recommended)

**Build and run with Docker:**

```bash
# Build the image
docker build -t all-your-tube .

# Run the container
docker run -d \
  --name all-your-tube \
  -p 1424:1424 \
  -v $(pwd)/downloads:/app/downloads \
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
      - ./downloads:/app/downloads
    environment:
      - AYT_WORKDIR=/app/downloads
```

### Running Locally

**Using the launch script (recommended):**

```bash
./launch.sh
```

**Using Poetry directly:**

```bash
poetry run all-your-tube
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
- **Static Files** (`src/all_your_tube/static/`): CSS and JavaScript for the web interface

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE)
file for details.
