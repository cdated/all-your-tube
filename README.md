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

### Running the Application

**Using the launch script (recommended):**

```bash
./launch.sh
```

**Using Poetry directly:**

```bash
poetry run python all-your-tube/main.py
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
poetry run pylint all-your-tube/main.py
```

**Code formatting:**

```bash
poetry run black all-your-tube/main.py
```

**Import sorting:**

```bash
poetry run isort all-your-tube/main.py
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

- **Main Application** (`all-your-tube/main.py`): Single-file Flask
  application
- **Templates** (`all-your-tube/templates/`): HTML templates for the web
  interface

### URL Structure

All routes use the `/yourtube` prefix:

- `/yourtube/`: Main download form
- `/yourtube/save`: POST endpoint for download submission
- `/yourtube/logs/<pid>`: Live log viewing page
- `/yourtube/stream/<pid>`: SSE endpoint for log streaming
- `/yourtube/log_desc/<pid>`: Get download description from logs

## Dependencies

- Flask: Web framework
- pygtail: Log file tailing for live updates
- werkzeug: WSGI utilities and proxy handling
- yt-dlp: YouTube downloader (external dependency)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE)
file for details.
