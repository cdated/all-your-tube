FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install yt-dlp and poetry
RUN pip install --no-cache-dir \
    yt-dlp~=2025.8.0 \
    poetry~=2.1.0

# Set work directory
WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock* README.md ./
COPY src/ ./src/

# Configure poetry: don't create virtual env, install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Create work directory for downloads
RUN mkdir -p /app/downloads

# Set environment variables
ENV AYT_WORKDIR=/app/downloads
ENV AYT_HOST=0.0.0.0
ENV AYT_PORT=1424

# Expose port
EXPOSE 1424

# Create non-root user
RUN useradd -m -u 1000 app && chown -R app:app /app
USER app

# Run the application
CMD ["poetry", "run", "all-your-tube"]
