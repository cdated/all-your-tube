# all-your-tube

A simple Flask web UI for yt-dlp (YouTube downloader) that provides a web
form to submit download requests and stream real-time download progress logs.

## Features

- Web-based interface for yt-dlp downloads
- Real-time log streaming using Server-Sent Events (SSE)
- Background download processing
- Directory organization for downloads
- Configurable yt-dlp arguments

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

1. Open your browser and navigate to `http://localhost:1424/yourtube/` (or
   your configured host/port)
2. Enter a YouTube URL in the form
3. Optionally specify a subdirectory for organization
4. Click "Download" to start the process
5. View real-time logs by following the provided link

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
- **Log Monitoring** (`src/all_your_tube/log_monitoring.py`): Real-time file
  monitoring using watchdog
- **Templates** (`src/all_your_tube/templates/`): HTML templates for the web interface
- **Static Files** (`src/all_your_tube/static/`): CSS and other static assets

### URL Structure

All routes use the `/yourtube` prefix:

- `/yourtube/`: Main download form
- `/yourtube/save`: POST endpoint for download submission
- `/yourtube/logs/<pid>`: Live log viewing page
- `/yourtube/stream/<pid>`: SSE endpoint for log streaming
- `/yourtube/log_desc/<pid>`: Get download description from logs

## Dependencies

- Flask: Web framework
- watchdog: Filesystem event monitoring for real-time log updates
- werkzeug: WSGI utilities and proxy handling
- yt-dlp: YouTube downloader (external dependency)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE)
file for details.
