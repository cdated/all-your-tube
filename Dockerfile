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

# Configure poetry: don't create virtual env, install dependencies only (no dev)
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-interaction --no-ansi

# Create non-root user first
RUN useradd -m -u 1000 app

# Create work and log directories with proper ownership
RUN mkdir -p /app/downloads /app/logs /app/downloads/logs && \
    chown -R app:app /app && \
    chmod -R 755 /app

# Set environment variables
ENV AYT_WORKDIR=/app/downloads
ENV AYT_HOST=0.0.0.0
ENV AYT_PORT=1424

# Expose port
EXPOSE 1424

# Switch to non-root user
USER app

# Add src to Python path and run the application
ENV PYTHONPATH=/app/src
CMD ["python", "-m", "all_your_tube.app"]
